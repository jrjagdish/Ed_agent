from agent_runner import agent_worker

async def start_process(user_input:dict):
    print("🤖 Agent is waking up...")
    
   
    # This is what starts the execution!
    final_output = app.invoke(user_input)
    
    # print("\n--- DONE ---")
    # print("Summary:", final_output["summary"])
    # print("\nMCQs:", final_output["mcqs"])
    total_cost = calculate_cost(final_output["tokens"])
    # print(f"\nEstimated Cost: ${total_cost}")
    return {
        "Summary":final_output["summary"],
        "MCQs":final_output["mcqs"],
        "Estimated Cost":total_cost
    }

def calculate_cost(tokens_dict):
    # Prices per 1 million tokens (Estimate for 2026)
    PRICES = {
        "gemini_flash_input": 0.10 / 1_000_000,
        "gemini_flash_output": 0.40 / 1_000_000,
        "groq_llama_input": 0.05 / 1_000_000,
        "groq_llama_output": 0.08 / 1_000_000,
    }

    gemini_cost = (tokens_dict['gemini_input'] * PRICES["gemini_flash_input"]) + \
                  (tokens_dict['gemini_output'] * PRICES["gemini_flash_output"])
    
    groq_cost = (tokens_dict['groq_input'] * PRICES["groq_llama_input"]) + \
                (tokens_dict['groq_output'] * PRICES["groq_llama_output"])
    
    return round(gemini_cost + groq_cost, 6)    

if __name__ == "__main__":
    start_process()
   
