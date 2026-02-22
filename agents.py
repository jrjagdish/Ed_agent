from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
import os
import dotenv
from state import GraphState

dotenv.load_dotenv()

gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", temperature=0, google_api_key=os.getenv("GOOGLE_API_KEY")
)
groq_model = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0, groq_api_key=os.getenv("GROQ_API_KEY")
)


def generate_mcq(state: GraphState) -> GraphState:
    input_text = state.get("input_text", "EMPTY")

    if isinstance(input_text, set):
        input_text = next(iter(input_text), "EMPTY")
    

    if not state.get("input_text"):
        return {"mcqs": "ERROR: No input text found in state."}

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert at creating educational MCQs. Use ONLY the provided text. Do NOT use outside knowledge."
                "IMPORTANT RULES: \n"
                "1. Do NOT use phrases like 'according to the text' or 'as mentioned in the provided text'.\n"
                "2. Each question must be self-contained and sound like a real exam question.\n"
                "3. Ensure the questions are clear and focused on the subject matter itself (e.g., Photosynthesis).",
            ),
            (
                "human",
                "Generate 10 multiple choice questions from the following text:\n\n{text}\n\nFormat the output as given below and don't use markdown format :"
                """Q[Number]: [Question text]
            A. [Option]
            B. [Option]
            C. [Option]
            D. [Option]
            Answer: [Letter]
            Explanation: [Brief reason]
                """,
            ),
        ]
    )
    chain = prompt | gemini_model
    response = chain.invoke({"text": state.get("input_text")})
    usage = response.usage_metadata

    return {
        "mcqs": response.content,
        "tokens": {
            "gemini_input": usage["input_tokens"],
            "gemini_output": usage["output_tokens"],
        },
    }


def generate_summary(state: GraphState) -> GraphState:
    response = groq_model.invoke(
        f"Read the following text concisely: {state['input_text']} and provide proper notes in markdown format."
    )
    usage = response.usage_metadata
    return {
        "summary": response.content,
        "tokens": {
            "groq_input": usage["input_tokens"],
            "groq_output": usage["output_tokens"],
        },
    }
