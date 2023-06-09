from colorama import Fore, Style

from autogpt.app import execute_command, get_command
from autogpt.chat import chat_with_ai, create_chat_message
from autogpt.config import Config
from autogpt.json_utils.json_fix_llm import fix_json_using_multiple_techniques
from autogpt.json_utils.utilities import validate_json
from autogpt.logs import logger, print_assistant_thoughts
from autogpt.speech import say_text
from autogpt.spinner import Spinner
from autogpt.utils import clean_input
from autogpt.database import db
from autogpt.models import Agent
import json





class Agent:
    """Agent class for interacting with Auto-GPT.

    Attributes:
        ai_name: The name of the agent.
        memory: The memory object to use.
        full_message_history: The full message history.
        next_action_count: The number of actions to execute.
        system_prompt: The system prompt is the initial prompt that defines everything the AI needs to know to achieve its task successfully.
        Currently, the dynamic and customizable information in the system prompt are ai_name, description and goals.

        triggering_prompt: The last sentence the AI will see before answering. For Auto-GPT, this prompt is:
            Determine which next command to use, and respond using the format specified above:
            The triggering prompt is not part of the system prompt because between the system prompt and the triggering
            prompt we have contextual information that can distract the AI and make it forget that its goal is to find the next task to achieve.
            SYSTEM PROMPT
            CONTEXTUAL INFORMATION (memory, previous conversations, anything relevant)
            TRIGGERING PROMPT

        The triggering prompt reminds the AI about its short term meta task (defining the next task)
    """

    def __init__(
        self,
        unique_id,
        ai_name,
        memory,
        full_message_history,
        next_action_count,
        system_prompt,
        triggering_prompt,
    ):
        self.unique_id = unique_id
        self.ai_name = ai_name
        self.memory = memory
        self.full_message_history = full_message_history
        self.next_action_count = next_action_count
        self.system_prompt = system_prompt
        self.triggering_prompt = triggering_prompt

        agent = Agent.query.filter_by(unique_id=unique_id_db).first()
        
        if agent:
            unique_id=self.unique_id,
            self.ai_name = agent.ai_name
            self.memory = agent.memory
            self.full_message_history = agent.full_message_history
            self.next_action_count = agent.next_action_count
            self.system_prompt = agent.system_prompt
            self.triggering_prompt = agent.triggering_prompt
        else:
        # Otherwise, create a new agent with the specified unique_id_db
            self.unique_id_db = unique_id_db
            agent = Agent(unique_id=self.unique_id_db,
                        ai_name=self.ai_name,
                        memory=self.memory,
                        full_message_history=self.full_message_history,
                        next_action_count=self.next_action_count,
                        system_prompt=self.system_prompt,
                        triggering_prompt=self.triggering_prompt)
        db.session.add(agent)
        db.session.commit()

    def update_user_input(self, new_user_input):
        self.user_input = new_user_input
    
    
    def start_interaction_loop(self, user_input=None):
        
        # Retrieve Agent object from database using unique ID
        agent = Agent.query.filter_by(unique_id=self.unique_id).first()

        # Update Agent object properties with latest values
        agent.next_action_count = self.next_action_count
        agent.memory = self.memory
        agent.system_prompt = self.system_prompt
        agent.triggering_prompt = self.triggering_prompt
        agent.full_message_history = self.full_message_history
        
        # Interaction Loop
        cfg = Config()
        loop_count = 0
        command_name = None
        arguments = None    
        print(user_input)    
        messages = [msg.get("message", {}).get("role", "") + ": " + msg.get("message", {}).get("content", "") for msg in self.full_message_history]

        while True:
            # Discontinue if continuous limit is reached.
            loop_count += 1
            if (
                cfg.continuous_mode
                and cfg.continuous_limit > 0
                and loop_count > cfg.continuous_limit
            ):
                logger.typewriter_log(
                    "Continuous Limit Reached: ", Fore.YELLOW, f"{cfg.continuous_limit}"
                )
                break

            # Send message to AI, get response
            with Spinner("Thinking... "):
                assistant_reply = chat_with_ai(
                    self.system_prompt,
                    self.triggering_prompt,
                    self.full_message_history,
                    self.memory,
                    cfg.fast_token_limit,
                )  # TODO: This hardcodes the model to use GPT3.5. Make this an argument

            assistant_reply_json = fix_json_using_multiple_techniques(assistant_reply)

            # Print Assistant thoughts
            if assistant_reply_json != {}:
                validate_json(assistant_reply_json, "llm_response_format_1")
                # Get command name and arguments
                try:
                    print_assistant_thoughts(self.ai_name, assistant_reply_json)
                    command_name, arguments = get_command(assistant_reply_json)
                    # command_name, arguments = assistant_reply_json_valid["command"]["name"], assistant_reply_json_valid["command"]["args"]
                    if cfg.speak_mode:
                        say_text(f"I want to execute {command_name}")
                except Exception as e:
                    logger.error("Error: \n", str(e))

            if not cfg.continuous_mode and self.next_action_count == 0:
                ### GET USER AUTHORIZATION TO EXECUTE COMMAND ###
                # Get key press: Prompt the user to press enter to continue or escape
                # to exit
                logger.typewriter_log(
                    "NEXT ACTION: ",
                    content=f"COMMAND = {command_name}  "
                            f"ARGUMENTS = {arguments}",
)
              
                prompt_text = (
                    "Enter 'y' to authorise command, 'y -N' to run N continuous "
                    "commands, 'n' to exit program, or enter feedback for "
                    f"{self.ai_name}..."
                )
                if not user_input:
                    return prompt_text
              
                print(
                    "Enter 'y' to authorise command, 'y -N' to run N continuous "
                    "commands, 'n' to exit program, or enter feedback for "
                    f"{self.ai_name}...",
                    flush=True,
                )
          
                while True:
                    
                    if user_input.lower().strip() == "y":
                        user_input = "GENERATE NEXT COMMAND JSON"
                        break
                    elif user_input.lower().strip() == "":
                        print("Invalid input format.")
                        continue
                    elif user_input.lower().startswith("y -"):
                        try:
                            self.next_action_count = abs(
                                int(user_input.split(" ")[1])
                            )
                            print("nombre!!!")
                            user_input = "GENERATE NEXT COMMAND JSON"
                        except ValueError:
                            print(
                                "Invalid input format. Please enter 'y -n' where n is"
                                " the number of continuous tasks."
                            )
                            continue
                 
                        break                        
                        
                    elif user_input.lower() == "n":
                        user_input = "EXIT"                        
                        break
                    else:
                        user_input = user_input
                        command_name = "human_feedback"                        
                        break
                if self.next_action_count == 0:
                    return(prompt_text)

                if user_input == "GENERATE NEXT COMMAND JSON":
                    logger.typewriter_log(
                        "-=-=-=-=-=-=-= COMMAND AUTHORISED BY USER -=-=-=-=-=-=-=",
                        Fore.MAGENTA,
                        "",
                    )
               
                elif user_input == "EXIT":
                    print("Exiting...", flush=True)                    
                    break
              
            else:
                # Print command
                logger.typewriter_log(
                    "NEXT ACTION: ",
                        content=f"COMMAND = {command_name}  "
                                f"ARGUMENTS = {arguments}",
                )
          

            # Execute command
            if command_name is not None and command_name.lower().startswith("error"):
                result = (
                    f"Command {command_name} threw the following error: {arguments}"
                )
            
            elif command_name == "human_feedback":
                result = f"Human feedback: {user_input}"
            else:
                result = (
                    f"Command {command_name} returned: "
                    f"{execute_command(command_name, arguments)}"
                )
                if self.next_action_count > 0:
                    self.next_action_count -= 1
          
            memory_to_add = (
                f"Assistant Reply: {assistant_reply} "
                f"\nResult: {result} "
                f"\nHuman Feedback: {user_input} "
            )
           
            self.memory.add(memory_to_add)

            # Check if there's a result from the command append it to the message
            # history
           
            if result is not None:
                print(f"Role: system, Content: {result}")  # Add this line for debugging
                self.full_message_history.append(create_chat_message("system", result))
                logger.typewriter_log("SYSTEM: ", Fore.YELLOW, result)
               
            else:
                self.full_message_history.append(
                    create_chat_message("system", "Unable to execute command")
                )
             
                logger.typewriter_log(
                    "SYSTEM: ", Fore.YELLOW, "Unable to execute command"
                )
                
            
