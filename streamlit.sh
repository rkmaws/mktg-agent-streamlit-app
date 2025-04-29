#!/bin/bash
# Ranjith Krishnamoorthy 2024

# Check for COGNITO_SECRET_NAME env variable
if [ -z "$COGNITO_SECRET_NAME" ]; then
    echo "Error: COGNITO_SECRET_NAME environment variable is not set"
    echo "Please set the environment variable: export COGNITO_SECRET_NAME=<secret_name>"
    exit 1
fi
# check for profile
if [ -z "$AWS_PROFILE" ]; then
    echo "Warning: AWS_PROFILE environment variable is not set."
    echo "Please set the environment variable: export AWS_PROFILE=<profile_name>"
    echo "Will be using default profile. Make sure this is the right environment"
fi
# aws sso login --profile $profile
streamlit run app.py \
    --server.runOnSave true \
    # --theme.base "light" \
    # --theme.backgroundColor "#333333" \
    # --theme.primaryColor "#CCC8AA" \
    # --theme.secondaryBackgroundColor "#777777" \
    # --ui.hideTopBar "true" \
    # --client.toolbarMode "minimal" \
    -- \
    --profile $AWS_PROFILE
    #--theme.base "light"
