#!/usr/bin/env python

# Copyright 2024 Amazon.com and its affiliates; all rights reserved.
# This file is AWS Content and may not be duplicated or distributed without permission
import sys
from pathlib import Path
import datetime
import traceback
import yaml
import uuid
from textwrap import dedent
import os
import argparse
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.bedrock_agent import Agent, SupervisorAgent, Task, region, account_id
import logging
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
task_yaml_path = os.path.join(current_dir, "tasks.yaml")
agent_yaml_path = os.path.join(current_dir, "agents.yaml")

def main(args):

    if args.recreate_agents == "false":
        Agent.set_force_recreate_default(False)
    else:
        Agent.set_force_recreate_default(True)
        Agent.delete_by_name("marketing_planning_agent", verbose=True)
    if args.clean_up == "true":
        Agent.delete_by_name("marketing_planning_agent", verbose=True)
        Agent.delete_by_name("lead_market_analyst", verbose=True)
        Agent.delete_by_name("chief_strategist", verbose=True)
        Agent.delete_by_name("creative_director", verbose=True)
        Agent.delete_by_name("content_writer", verbose=True)
        Agent.delete_by_name("formatted_report_writer", verbose=True)
        
    else:
        inputs = {
            'product_name': args.product_name,
            'project_description': args.project,
            'feedback_iteration_count': args.iterations,
        }    

        with open(task_yaml_path, 'r') as file:
            task_yaml_content = yaml.safe_load(file)

        research_task = Task('research_task', task_yaml_content, inputs)
        marketing_strategy_task = Task('marketing_strategy_task', task_yaml_content, inputs)
        campaign_idea_task =  Task('campaign_idea_task', task_yaml_content, inputs)
        copy_creation_task = Task('copy_creation_task', task_yaml_content, inputs)
        detailed_campaign_task = Task('detailed_campaign_task', task_yaml_content, inputs)
        iterative_revisions_task = Task('iterative_revisions_task', task_yaml_content, inputs)
        final_report_output_task = Task('final_report_output_task', task_yaml_content, inputs)
            
        web_search_tool = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:web_search",
            "definition":{
                "name": "web_search",
                "description": "Searches the web for information",
                "parameters": {
                    "search_query": {
                        "description": "The query to search the web with",
                        "type": "string",
                        "required": True,
                    },
                    "target_website": {
                        "description": "The specific website to search including its domain name. If not provided, the most relevant website will be used",
                        "type": "string",
                        "required": False,
                    },
                    "topic": {
                        "description": "The topic being searched. 'news' or 'general'. Helps narrow the search when news is the focus.",
                        "type": "string",
                        "required": False,
                    },
                    "days": {
                        "description": "The number of days of history to search. Helps when looking for recent events or news.",
                        "type": "string",
                        "required": False,
                    },
                },
            },
        }

        set_value_for_key = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition":{
                "name": "set_value_for_key",
                "description": " Stores a key-value pair in a DynamoDB table. Creates the table if it doesn't exist.",
                "parameters": {
                    "key": {
                        "description": "The name of the key to store the value under.",
                        "type": "string",
                        "required": True,
                    },
                    "value": {
                        "description": "The value to store for that key name.",
                        "type": "string",
                        "required": True,
                    },
                    "table_name": {
                        "description": "The name of the DynamoDB table to use for storage.",
                        "type": "string",
                        "required": True,
                    }
                },
            },
        }

        get_key_value = {
            "code":f"arn:aws:lambda:{region}:{account_id}:function:working_memory",
            "definition":{
                "name": "get_key_value",
                "description": "Retrieves a value for a given key name from a DynamoDB table.",
                "parameters": {
                    "key": {
                        "description": "The name of the key to store the value under.",
                        "type": "string",
                        "required": True,
                    },
                    "table_name": {
                        "description": "The name of the DynamoDB table to use for storage.",
                        "type": "string",
                        "required": True,
                    }
                },
            },
        }

        with open(agent_yaml_path, 'r') as file:
            agent_yaml_content = yaml.safe_load(file)

        lead_market_analyst = Agent('lead_market_analyst', agent_yaml_content,
                                    tools=[web_search_tool, set_value_for_key, get_key_value])
        chief_strategist = Agent('chief_strategist', agent_yaml_content,
                                    tools=[web_search_tool, set_value_for_key, get_key_value])
        creative_director = Agent('creative_director', agent_yaml_content,
                                  tools=[web_search_tool, set_value_for_key, get_key_value])
        content_creator = Agent('content_writer', agent_yaml_content,
                                  tools=[web_search_tool, set_value_for_key, get_key_value])
        formatted_report_writer = Agent('formatted_report_writer', agent_yaml_content,
                                  tools=[web_search_tool, set_value_for_key, get_key_value])
        
        logger.info("\n\nCreating marketing_strategy_agent as a supervisor agent...\n\n")
        marketing_planning_agent = SupervisorAgent("marketing_planning_agent", agent_yaml_content,
                                    [lead_market_analyst, chief_strategist, 
                                    content_creator, creative_director, 
                                    formatted_report_writer], 
                                    verbose=False)
        
        if args.recreate_agents == "false":
            logger.info("\n\nInvoking supervisor agent...\n\n")

            time_before_call = datetime.datetime.now()
            logger.info(f"time before call: {time_before_call}\n")
            try:
                folder_name = "startup-advisor-" + str(uuid.uuid4())
                result = marketing_planning_agent.invoke_with_tasks([
                                research_task, marketing_strategy_task, 
                                campaign_idea_task, copy_creation_task, 
                                detailed_campaign_task, iterative_revisions_task,
                                final_report_output_task
                            ],
                            additional_instructions=dedent(f"""
                                Use a single Working Memory table for this entire set of tasks, with 
                                table name: {folder_name}. Tell your collaborators this table name as part of 
                                every request, so that they are not confused and they share state effectively.
                                The keys they use in that table will allow them to keep track of any number 
                                of state items they require. When you have completed all tasks, summarize 
                                your work, and share the table name so that all the results can be used and 
                                analyzed."""),
                            processing_type="sequential", 
                            enable_trace=True, trace_level=args.trace_level,
                            verbose=True)
                logger.info(result)
            except Exception as e:
                logger.error(e)
                traceback.print_exc()
                pass

            duration = datetime.datetime.now() - time_before_call
            logger.info(f"\nTime taken: {duration.total_seconds():,.1f} seconds")
        else:
            logger.info("Recreated agents.")
        


if __name__ == '__main__':
    default_inputs = {
        'product_name': 'AWS Startup Credits',
        'project_description': dedent("""
AWS is the leading cloud service provider 
The project is to build an innovative marketing strategy to showcase AWS Startup credits programs' advanced 
offerings, emphasizing ease of use, cost effectiveness, productivity, and scalability. 
Target startup founders, highlighting success stories and transformative 
potential. Be sure to include a draft for a video ad.
"""),
        'iterations': "1"
    }    

    parser = argparse.ArgumentParser()

    parser.add_argument("--recreate_agents", required=False, default='true', help="False if reusing existing agents.")
    parser.add_argument("--product_name", required=False, 
                        default=default_inputs['product_name'],
                        help="The product or service offering")
    parser.add_argument("--iterations", required=False, 
                        default=default_inputs['iterations'],
                        help="The number of rounds of feedback to use when producing the campaign report")
    parser.add_argument("--project", required=False, 
                        default=default_inputs['project_description'],
                        help="The project that needs a marketing strategy.")
    parser.add_argument("--trace_level", required=False, default="core", help="The level of trace, 'core', 'outline', 'all'.")
    parser.add_argument(
        "--clean_up",
        required=False,
        default="false",
        help="Cleanup all infrastructure.",
    )
    args = parser.parse_args()
    main(args)
