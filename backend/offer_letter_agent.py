import os
import pandas as pd
from functools import lru_cache
from dotenv import load_dotenv
import logging
from datetime import datetime
from backend.utils.generator import get_agent_with_fallback, test_llm

load_dotenv()
logger = logging.getLogger(__name__)

from backend.utils.loader import load_pdf
from backend.utils.chunker import chunk_text
from backend.utils.embedder import get_vectorstore

DATA_DIR = "backend/data"
PDF_FILES = ["HR Leave Policy.pdf", "HR Travel Policy.pdf", "HR Offer Letter.pdf"]
EMPLOYEE_CSV = "Employee_List.csv"

@lru_cache(maxsize=1)
def cached_vectorstore():
    try:
        docs = []
        for file in PDF_FILES:
            path = os.path.join(DATA_DIR, file)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing: {file}")
            raw_text = load_pdf(path)
            docs.extend(chunk_text(raw_text))
        return get_vectorstore(docs)
    except Exception as e:
        logger.error(f"VectorStore setup error: {str(e)}")
        raise RuntimeError(f"VectorStore setup error: {str(e)}")

def get_employee_record(name: str) -> dict:
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, EMPLOYEE_CSV))
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]
        if "employee_name" not in df.columns:
            raise RuntimeError("Missing 'Employee Name' column in CSV.")

        record = df[df["employee_name"].str.lower() == name.lower()]
        if record.empty:
            logger.warning(f"No employee found with name: {name}")
            raise ValueError(f"No employee found with name: {name}")
        return record.iloc[0].to_dict()
    except Exception as e:
        logger.error(f"CSV read error: {str(e)}")
        raise RuntimeError(f"CSV read error: {str(e)}")

def generate_offer_for(name: str):
    try:
        employee = get_employee_record(name)
        if employee is None:
            return {"error": f"Employee '{name}' not found in Employee_List.csv"}

        vectorstore = cached_vectorstore()

        input_data = {
            "name": employee["employee_name"],
            "band": employee["band"],
            "team": employee["department"],
            "location": employee["location"],
            "joining_date": employee["joining_date"],
            "salary_breakup": {
                "base": employee["base_salary_(inr)"],
                "bonus": employee["performance_bonus_(inr)"],
                "retention": employee["retention_bonus_(inr)"],
                "total": employee["total_ctc_(inr)"]
            },
            "query": f"Offer letter for {employee['employee_name']} joining {employee['department']} at {employee['location']} on {employee['joining_date']}",
            "generated_date": datetime.now().strftime("%B %d, %Y")
        }

        agent = get_agent_with_fallback(vectorstore)
        offer_letter = agent.invoke(input_data)

        logger.info(f"Successfully generated offer letter for: {name} using {agent.__class__.__name__}")
        return {
            "offer_letter": offer_letter,
            "method": "llm_or_template_fallback",
            "employee_details": {
                "name": employee["employee_name"],
                "band": employee["band"],
                "department": employee["department"],
                "location": employee["location"],
                "joining_date": employee["joining_date"],
                "salary": employee["total_ctc_(inr)"]
            },
            "generated_on": input_data["generated_date"]
        }
    except Exception as e:
        logger.error(f"Offer generation failed for {name}: {str(e)}")
        raise RuntimeError(f"Offer generation failed: {str(e)}")

def check_system_status():
    try:
        vectorstore = cached_vectorstore()
        df = pd.read_csv(os.path.join(DATA_DIR, EMPLOYEE_CSV))
        employee_count = len(df)
        llm_status = test_llm()  # Tests OpenRouter.ai connectivity
        llm_message = "OpenRouter.ai LLM available" if llm_status else "OpenRouter.ai LLM unavailable, using template fallback"

        logger.info("System status check completed successfully")
        return {
            "status": "healthy",
            "message": f"System is working properly. {llm_message}",
            "vectorstore": "initialized",
            "employee_records": employee_count,
            "generation_method": "llm_or_template_fallback"
        }
    except Exception as e:
        logger.error(f"System status check failed: {str(e)}")
        return {
            "status": "error",
            "message": f"System error: {str(e)}"
        }

def check_openrouter_status():
    """Check the status of OpenRouter.ai LLM"""
    try:
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not set in environment")
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="openrouter/auto"
        )
        llm.invoke("Test OpenRouter.ai connectivity")
        logger.info("OpenRouter.ai LLM test successful")
        return {"status": "available", "message": "OpenRouter.ai LLM is working"}
    except Exception as e:
        logger.warning(f"OpenRouter.ai LLM test failed: {str(e)} - using template fallback")
        return {"status": "unavailable", "message": f"OpenRouter.ai error: {str(e)} - using template fallback"}

def list_employees():
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, EMPLOYEE_CSV))
        df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

        employees = []
        for _, row in df.iterrows():
            employees.append({
                "name": row.get("employee_name", ""),
                "band": row.get("band", ""),
                "department": row.get("department", ""),
                "location": row.get("location", ""),
                "joining_date": row.get("joining_date", ""),
                "salary": row.get("total_ctc_(inr)", "")
            })

        logger.info(f"Successfully listed {len(employees)} employees")
        return {"employees": employees, "count": len(employees)}
    except Exception as e:
        logger.error(f"Failed to load employee list: {str(e)}")
        raise RuntimeError(f"Failed to load employee list: {str(e)}")
