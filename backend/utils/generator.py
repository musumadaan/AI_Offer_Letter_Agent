from dotenv import load_dotenv  # Load .env file if run standalone; otherwise, rely on main.py
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableMap, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
import os
import logging
import json
from datetime import datetime
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

load_dotenv()  # Ensure environment variables are loaded for standalone use

def get_openrouter_llm(api_key):
    """Initialize OpenRouter.ai LLM using ChatOpenAI with OpenRouter endpoint"""
    try:
        logger.debug(f"Attempting to initialize OpenRouter.ai LLM with API key: {api_key[:4]}...[REDACTED]")
        llm = ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="openrouter/auto",  # OpenRouter auto-selects the best model
            temperature=0.3,
            max_tokens=1024,
            top_p=0.9
        )
        test_result = llm.invoke("Generate a test sentence.")
        logger.info("OpenRouter.ai LLM initialization - SUCCESS")
        return llm, "openrouter/auto"
    except Exception as e:
        logger.warning(f"OpenRouter.ai LLM initialization failed: {str(e)}")
        return None, None

def get_working_llm():
    """Attempts to get a working LLM using OpenRouter.ai"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    logger.debug(f"Retrieved OPENROUTER_API_KEY from environment: {api_key[:4] if api_key else 'None'}...[REDACTED]")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return None, None

    logger.info("Trying OpenRouter.ai LLM...")
    llm, model_name = get_openrouter_llm(api_key)
    if llm:
        return llm, model_name

    logger.error("OpenRouter.ai LLM failed")
    return None, None

def get_agent(vectorstore):
    """Enhanced agent using OpenRouter.ai LLM with template fallback"""
    prompt = PromptTemplate.from_template("""
You are an HR assistant. Based on the following company policies:

{context}

Generate a professional offer letter for the following candidate:
- Name: {name}
- Position Band: {band}
- Team/Department: {team}
- Work Location: {location}
- Joining Date: {joining_date}
- Salary Details: {salary_breakup_str}

Create a formal, comprehensive offer letter that includes all necessary details, terms and conditions, and references relevant company policies from the context provided above.
""")

    # Try to get a working LLM
    llm, model_name = get_working_llm()
    if not llm:
        logger.warning("No LLM available. Using template fallback.")
        return get_template_based_agent(vectorstore)

    logger.info(f"Successfully initialized LLM: {model_name}")

    # Enhanced context retrieval function
    def get_context(inputs):
        try:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
            query = f"employment policies benefits {inputs['band']} {inputs['team']} offer letter terms conditions"
            docs = retriever.invoke(query)
            context_parts = []
            for doc in docs[:3]:  # Limit to top 3 documents
                content = doc.page_content[:500]  # Limit content length
                context_parts.append(content)
            context = "\n\n".join(context_parts)
            return context if context.strip() else "Standard company policies apply as per employee handbook."
        except Exception as e:
            logger.warning(f"Context retrieval failed: {e}")
            return "Standard company policies apply as per employee handbook."

    # Create the chain
    try:
        chain = RunnableMap({
            "context": RunnableLambda(get_context),
            "name": lambda x: x["name"],
            "band": lambda x: x["band"],
            "team": lambda x: x["team"],
            "location": lambda x: x["location"],
            "joining_date": lambda x: x["joining_date"],
            "salary_breakup_str": lambda x: json.dumps(x["salary_breakup"], indent=2)
        }) | prompt | llm | StrOutputParser()
        return chain
    except Exception as e:
        logger.error(f"Chain creation failed: {str(e)}")
        return get_template_based_agent(vectorstore)

def get_template_based_agent(vectorstore=None):
    """Enhanced template-based agent with vectorstore integration"""

    def generate_offer_letter(inputs):
        try:
            # Enhanced context retrieval
            relevant_policies = "• Standard company policies apply as per employee handbook."
            if vectorstore:
                try:
                    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
                    query = f"policies benefits {inputs.get('band', '')} {inputs.get('team', '')} employment"
                    docs = retriever.invoke(query)
                    policy_snippets = []
                    for doc in docs:
                        content = doc.page_content
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if any(keyword in line.lower() for keyword in [
                                'leave', 'vacation', 'policy', 'benefit', 'salary',
                                'working hours', 'probation', 'ctc', 'compensation',
                                'annual', 'medical', 'insurance', 'bonus', 'allowance']):
                                if len(line) > 20:
                                    policy_snippets.append(f"• {line}")
                    if policy_snippets:
                        relevant_policies = '\n'.join(policy_snippets[:8])
                except Exception as e:
                    logger.warning(f"Could not retrieve enhanced context: {str(e)}")

            # Enhanced salary breakdown formatting
            try:
                salary_items = []
                total_ctc = 0
                for k, v in inputs["salary_breakup"].items():
                    formatted_key = k.replace('_', ' ').title()
                    if isinstance(v, (int, float)):
                        salary_items.append(f"  - {formatted_key}: ₹{v:,.2f}")
                        total_ctc += v
                    else:
                        salary_items.append(f"  - {formatted_key}: {v}")
                salary_breakup_str = '\n'.join(salary_items)
                if total_ctc > 0:
                    salary_breakup_str += f"\n  - Total Annual CTC: ₹{total_ctc:,.2f}"
            except Exception as e:
                logger.warning(f"Salary formatting error: {str(e)}")
                salary_breakup_str = "Please refer to the detailed salary structure provided separately."

        except Exception as e:
            logger.warning(f"Context processing error: {str(e)}")
            relevant_policies = "• Standard company policies apply as per employee handbook."
            salary_breakup_str = "N/A"

        # Enhanced offer letter template with requested changes
        current_date = datetime.now().strftime("%Y-%m-%d")
        company_name = "ABC"
        company_address = "456 Corporate Drive, Los Angeles, CA 90001"  # Fake address

        offer_letter = f"""
[Company Letterhead]
{company_name}
{company_address}

Date: {current_date}

Dear {inputs['name']},

We are pleased to extend this formal offer of employment with our organization. After careful consideration of your qualifications and experience, we believe you will be a valuable addition to our team.

POSITION DETAILS

Position Band: {inputs['band']}
Department/Team: {inputs['team']}
Work Location: {inputs['location']}
Expected Date of Joining: {inputs['joining_date']}

COMPENSATION PACKAGE

Your annual compensation package is structured as follows:

{salary_breakup_str}

TERMS AND CONDITIONS

This employment offer is subject to the following terms and conditions based on our company policies:

{relevant_policies}

GENERAL CONDITIONS

• Employment is contingent upon successful completion of background verification and reference checks
• You will be subject to a probationary period as outlined in the company policy
• All employee benefits, allowances, and entitlements will be governed by the current employee handbook
• Working hours, leave policies, and reporting structure will be as per company standards
• This offer is confidential and remains valid for 7 business days from the date of this letter
• Any changes to this offer must be agreed upon in writing by both parties

ACCEPTANCE AND NEXT STEPS

To accept this offer, please:
1. Sign and return a copy of this letter
2. Complete the attached joining formalities checklist
3. Submit all required documentation as specified by HR

We are excited about the prospect of you joining our team and look forward to your positive response. Should you have any questions regarding this offer or require clarification on any aspect, please do not hesitate to contact our Human Resources department.

We welcome you to our organization and are confident that this will be the beginning of a mutually beneficial professional relationship.

Warm regards,
Aarti Nair
HR Business Partner
{company_name}

---
This offer letter was generated on {current_date}
For queries or clarifications, please contact HR at [hr@company.com]
"""

        return offer_letter.strip()

    return RunnableLambda(generate_offer_letter)

class RobustFallbackAgent:
    """Robust agent that tries OpenRouter.ai, then template fallback"""

    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.agent = get_agent(vectorstore)  # Use the full agent chain
        self._llm_agent, self._llm_model = get_working_llm()
        self._initialization_attempted = False

    def _initialize_llm(self):
        """Initialize LLM with OpenRouter.ai"""
        if not self._initialization_attempted:
            try:
                self._llm_agent, self._llm_model = get_working_llm()
                self._initialization_attempted = True
            except Exception as e:
                logger.warning(f"LLM initialization failed: {str(e)}")
                self._initialization_attempted = True

    def invoke(self, inputs):
        # Add timestamp
        inputs['generated_date'] = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Try to initialize LLM if not done yet
        self._initialize_llm()
        
        # Try LLM first if available, using the full agent chain
        if self._llm_agent:
            try:
                result = self.agent.invoke(inputs)  # Use the pre-built chain
                logger.info(f"Successfully used {self._llm_model} LLM generation")
                return result
            except Exception as e:
                logger.warning(f"{self._llm_model} LLM failed: {str(e)}. Using template fallback.")
        
        # Fallback to template
        result = self.agent.invoke(inputs) if isinstance(self.agent, RunnableLambda) else self.agent(inputs)
        logger.info("Successfully used template fallback")
        return result

# Updated factory functions
def get_agent_with_fallback(vectorstore):
    """Get robust agent with OpenRouter.ai and template fallback"""
    return RobustFallbackAgent(vectorstore)

def get_safe_agent(vectorstore):
    """Get template-only agent for guaranteed reliability"""
    return get_template_based_agent(vectorstore)

def test_llm():
    """Test LLM connectivity with OpenRouter.ai"""
    logger.info("Testing OpenRouter.ai LLM connectivity...")
    
    llm, model_name = get_working_llm()
    if llm:
        logger.info(f"✓ OpenRouter.ai LLM test successful using {model_name}")
        return True
    else:
        logger.error("✗ OpenRouter.ai LLM test failed")
        return False

def debug_llm():
    """Debug function to check LLM setup"""
    logger.info("=== LLM Debug Information ===")
    
    # Check OpenRouter API key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    logger.debug(f"Raw OPENROUTER_API_KEY value: {openrouter_key[:4] if openrouter_key else 'None'}...[REDACTED]")
    if openrouter_key:
        logger.info(f"✓ OPENROUTER_API_KEY is set (length: {len(openrouter_key)})")
    else:
        logger.error("✗ OPENROUTER_API_KEY is not set")
    
    # Check imports
    try:
        from langchain_openai import ChatOpenAI
        logger.info("✓ langchain_openai import successful")
    except ImportError as e:
        logger.error(f"✗ langchain_openai import failed: {e}")
    
    # Test LLM
    test_llm()
    
    return True