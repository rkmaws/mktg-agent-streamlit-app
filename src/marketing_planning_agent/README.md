# Startup Advisor Agent

Have a new startup in mind, but haven't quite hired your marketing staff? Use this Startup Advisrt agent to do your market research, come up with campaign ideas, and write effective campaign copy. It uses a set of 5 sub-agents to get the job done these include Lead Market Analyst, Content Creator, Chief Conent Creator, Chief Stategist, and Agent Storage Manager.

![architecture](/images/architecture.gif)

## Prerequisites

1. Clone and install repository

```bash
git clone git@github.com:rkmaws/mktg-agent-streamlit-app.git

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r src/requirements.txt
```

2. Deploy Web Search tool

Follow instructions [here](/src/shared/web_search/).

3. Deploy Working Memory tool

Follow instructions [here](/src/shared/working_memory/).

## Usage & Sample Prompts


1. Deploy Amazon Bedrock Agents

```bash
python3 src/marketing_planning_agent/main.py \
--recreate_agents "true"
```

2. Invoke

```bash
python3 src/marketing_planning_agent/main.py \
--recreate_agents "false" \
--product_name "AWS Startup Credits" \
--project "AWS is the leading cloud service provider 
The project is to build an innovative marketing strategy to showcase AWS Startup credits programs' advanced 
offerings, emphasizing ease of use, cost effectiveness, productivity, and scalability. 
Target startup founders, highlighting success stories and transformative 
potential. Be sure to include a draft for a video ad."
```

3. Cleanup

```bash
python3 src/marketing_planning_agent/main.py \
--clean_up "true"
```

## License

This project is licensed under the Apache-2.0 License.