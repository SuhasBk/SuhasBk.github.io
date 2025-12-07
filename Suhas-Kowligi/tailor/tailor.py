import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents.stuff import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

# --- Configuration ---

# Load environment variables from .env file (for GOOGLE_API_KEY)
load_dotenv()

# Path to the folder containing your career data files (Master Resume, etc.)
# IMPORTANT: Create this folder and put your career data (.txt, .md, or .pdf) inside.
DOCUMENTS_FOLDER_PATH = "../"
CHROMA_DB_PATH = "./chroma_db_store"

# Cloud Models (Requires GOOGLE_API_KEY set in .env)
LLM_MODEL = "gemini-2.5-flash"  # Fast and cost-efficient for generation
EMBEDDING_MODEL = "models/gemini-embedding-001"

# --- RAG Core Functions ---

documents = []
master_latex = ""

def load_and_index_career_data():
    global master_latex
    """Loads documents, splits them, creates embeddings via Gemini API, and stores them in ChromaDB."""
    print("--- Starting Career Data Indexing ---")

    if not os.path.exists(DOCUMENTS_FOLDER_PATH):
        print(f"Error: Directory not found at {DOCUMENTS_FOLDER_PATH}. Please create it and add career documents.")
        return None

    # Load documents: Using TextLoader for text files and PyPDFDirectoryLoader for PDFs
    for file_name in os.listdir(DOCUMENTS_FOLDER_PATH):
        file_path = os.path.join(DOCUMENTS_FOLDER_PATH, file_name)
        if file_name.endswith('resume.tex'):
            documents.extend(TextLoader(file_path).load())
            master_latex = open(file_path).read()
        # elif file_name.endswith('.pdf'):
        #     documents.extend(PyPDFLoader(file_path).load())
        #     print(file_path)
        # else:
        #     exit('no data found!')

    if not documents:
        print("No documents found or loaded successfully in the career data folder.")
        return None

    print(f"Loaded {len(documents)} document pages/files for indexing.")

    # 1. Split Documents into manageable chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1500,  # Larger chunks for resume data might be useful to keep context
        chunk_overlap=200,
        length_function=len
    )
    splits = text_splitter.split_documents(documents)
    print(f"Created {len(splits)} document chunks.")

    # 2. Create Embeddings via Gemini API
    print(f"Initializing Gemini Embeddings with model: {EMBEDDING_MODEL}")
    # The API key is read automatically from the GOOGLE_API_KEY environment variable
    embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    # 3. Create and Persist Vector Store
    print(f"Creating and persisting ChromaDB at: {CHROMA_DB_PATH}")
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CHROMA_DB_PATH
    )
    print("--- Indexing Complete! Vector Store is ready. ---")
    return vectorstore

def generate_tailored_resume_content(vectorstore: Chroma, job_description: str):
    """
    Performs RAG to match career data to the job description and generates tailored content.
    """
    print("\n--- Running AI Resume Tailor ---")
    
    # 1. Setup LLM and Retriever
    llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.2) # Lower temperature for factual rewriting
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8}) # Retrieve more chunks to match more JD requirements

    # 2. Define the Prompt Template
    system_prompt = (
        "You are an expert resume editor with deep knowledge of LaTeX. Your task is to take the user's master LaTeX resume, provided "
        "as [RETRIEVED CONTEXT], and modify it to align with the [JOB DESCRIPTION]."
        "\n\n**CRITICAL INSTRUCTIONS:**"
        "\n1. **Preserve Structure:** You MUST NOT change the LaTeX preamble, document structure, or custom commands. The overall template is fixed."
        "\n2. **Targeted Edits:** Rewrite the bullet points within the `\\job{{...}}` sections to highlight skills from the job description. Pick and choose appropriate `\\projects{{...}}` and `\\skills{{...}}` based on job description. Surgically add/remove skills from existing categories. Do NOT modify the categories themselves. Make sure ONLY TOP 3 relevant projects are selected based on job description keywords. Compress the project bullet points into one single bullet point which captures impact. Include/exclude relevant certifications only if required by job description"
        "\n3. **Full Document Output:** Your final output MUST be the complete, modified master latex. Do NOT change tags. Just fill in the resume parts. Do not wrap the contents in latex markdown tags!!!"
        "\n\n[JOB DESCRIPTION]: {query_job_description}"
        "\n\n[RETRIEVED CONTEXT]: {context}" \
        "\n\n[master latex]: {master_latex}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "Rewrite my resume content based on the job description."),
        ]
    )

    # 3. Build the RAG Chain
    document_chain = create_stuff_documents_chain(llm, prompt)

    # Use a Runnable Map to correctly package the JD (query) for both the retriever and the LLM
    rag_chain = create_retrieval_chain(
        retriever,
        document_chain
    )
    
    # 4. Invoke the Chain
    # We pass the JD string as the 'input' (for the retriever) AND 'query_job_description' (for the LLM prompt)
    response = rag_chain.invoke({"input": job_description, "query_job_description": job_description, "master_latex": master_latex})

    # 5. Output Result
    print("\n--- GENERATED TAILORED CONTENT ---")
    new_latex = response["answer"]

    with open('../resume_draft.tex', 'w') as new_resume:
        new_resume.write(new_latex)

    # Show source validation
    sources = [os.path.basename(doc.metadata.get('source', 'Unknown Source')) for doc in response["context"]]
    print("\n(Successfully matched to career data from the following source files: " + ", ".join(set(sources)) + ")")


# --- Main Execution ---

def generate(job_description):
    # 1. Ensure document folder exists
    if not os.path.exists(DOCUMENTS_FOLDER_PATH):
        os.makedirs(DOCUMENTS_FOLDER_PATH)
        print(f"Created directory: {DOCUMENTS_FOLDER_PATH}. Please place your master resume data (.txt, .md, or .pdf) here and run again.")
        return False
    else:
        # 2. Index the career documents
        vectorstore = load_and_index_career_data()
        if vectorstore:
            # 3. Run the Resume Tailoring Process
            generate_tailored_resume_content(vectorstore, job_description)
    return True

if __name__ == "__main__":
    job_description = """
    Job Description:

Java Backend development (coding, OOPs concept, Junit Testing, Database etc)

MUST Experience working with Java 8 Spring Cloud Hibernate Spring Boot

MUST Experience with Microservices Rest services Soap development

MUST Solid grasp of web and backend application development

MUST Knowledge of Domain Driven Design concepts and microservices REST API design and implementation

MUST Familiar with secure development best practices knowledge of Security principles Encryption Authentication Authorization etc

MUST Knowledge of Java build tools and dependency management Gradle maven

MUST Database experience at least 1 Postgres Oracle MySQL NoSQL databases MongoDB Cassandra Neo4J


MUST Strong written and verbal skills:

Preferred Experience with Nodejs React Backbone or other client side MVC technologies is a plus

Preferred Experience in continuous integration build tools Jenkins SonarQube JIRA Nexus Confluence GIT Bit Bucket Maven Gradle Run Deck is a plus

Preferred Experience working with GCP or any other cloud platform

Preferred Experience working with Agile methodology


Mandatory Skills : Hibernate, Java, Spring Cloud, Microservices, Spring, Spring Security, Spring Boot, Spring MVC, Spring Integration.
    """
    generate(job_description)