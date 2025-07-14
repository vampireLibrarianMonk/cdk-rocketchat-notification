#!/bin/bash

set -e

ALL_STACKS=(
  "CloudWatchAlarmStack"
  "LambdaStack"
  "RocketChatStack"
  "DiskMonitorStack"
  "EnvSetupStack"
)

function destroy_stack() {
  local STACK=$1
  echo "🗑️  Destroying $STACK..."
  cdk destroy "$STACK" --force
}

if [ "$#" -eq 0 ]; then
  echo "❌ No stack specified."
  echo "Usage:"
  echo "  ./destroy.sh all                # Destroy all stacks in reverse-dependency order"
  echo "  ./destroy.sh <StackName> [...] # Destroy one or more specific stacks"
  exit 1
fi

if [ "$1" == "all" ]; then
  for STACK in "${ALL_STACKS[@]}"; do
    destroy_stack "$STACK"
  done
else
  for STACK in "$@"; do
    destroy_stack "$STACK"
  done
fi

echo "✅ Destruction complete."
