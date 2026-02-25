"""
debug_bedrock.py — Run this FIRST before testing the full workflow.

Usage:
    python debug_bedrock.py

This script tests Bedrock connectivity completely independently of Strands,
the graph, and all agent code. If this fails, the problem is credentials or
network. If this passes, the problem is in the agent/graph layer.
"""

import os
import json
import boto3
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("debug_bedrock")

MODEL_ID = os.getenv(
    "MODEL_PLANNING",
    "arn:aws:bedrock:us-east-2:070797854596:"
    "inference-profile/us.meta.llama3-3-70b-instruct-v1:0",
)
REGION = os.getenv("AWS_REGION", "us-east-2")


def test_credentials():
    logger.info("=== TEST 1: AWS credentials ===")
    sts = boto3.client("sts", region_name=REGION)
    identity = sts.get_caller_identity()
    logger.info("Account: %s", identity["Account"])
    logger.info("UserId:  %s", identity["UserId"])
    logger.info("ARN:     %s", identity["Arn"])
    logger.info("✓ Credentials OK")


def test_bedrock_list():
    logger.info("=== TEST 2: List Bedrock foundation models ===")
    client = boto3.client("bedrock", region_name=REGION)
    response = client.list_foundation_models(byOutputModality="TEXT")
    models = response.get("modelSummaries", [])
    logger.info("Found %d text models in region %s", len(models), REGION)
    logger.info("✓ Bedrock API reachable")


def test_bedrock_converse():
    logger.info("=== TEST 3: Direct converse call ===")
    logger.info("Model:  %s", MODEL_ID)
    logger.info("Region: %s", REGION)

    client = boto3.client("bedrock-runtime", region_name=REGION)

    request = {
        "modelId": MODEL_ID,
        "system": [{"text": "You are a helpful assistant. Reply very briefly."}],
        "messages": [
            {"role": "user", "content": [{"text": "Say exactly: BEDROCK_OK"}]}
        ],
        "inferenceConfig": {"maxTokens": 50},
    }

    logger.debug("Request: %s", json.dumps(request, indent=2))

    response = client.converse(**request)

    logger.debug("Full response: %s", json.dumps(response, default=str, indent=2))

    content = response.get("output", {}).get("message", {}).get("content", [])
    text = content[0].get("text", "") if content else ""

    logger.info("Model replied: '%s'", text.strip())

    if not text.strip():
        raise ValueError("Model returned empty text — check model ID and region access")

    logger.info("✓ Converse API working")
    return text


def test_json_output():
    logger.info("=== TEST 4: JSON structured output ===")
    client = boto3.client("bedrock-runtime", region_name=REGION)

    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": "Return ONLY valid JSON. No prose. No markdown fences."}],
        messages=[{
            "role": "user",
            "content": [{"text": 'Return this exact JSON: {"status": "ok", "value": 42}'}]
        }],
        inferenceConfig={"maxTokens": 100},
    )

    content = response.get("output", {}).get("message", {}).get("content", [])
    text = content[0].get("text", "").strip() if content else ""
    logger.info("Raw response: '%s'", text)

    # Try to parse
    try:
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        parsed = json.loads(text)
        logger.info("Parsed JSON: %s", parsed)
        logger.info("✓ JSON output working")
    except json.JSONDecodeError as e:
        logger.error("Model did not return valid JSON: %s", e)
        logger.error("Raw text was: '%s'", text)
        raise


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Bedrock Connectivity Debug")
    print("=" * 60 + "\n")

    steps = [
        ("Credentials",        test_credentials),
        ("Bedrock list models", test_bedrock_list),
        ("Converse API",        test_bedrock_converse),
        ("JSON output",         test_json_output),
    ]

    for name, fn in steps:
        try:
            fn()
            print(f"  ✓ {name}\n")
        except Exception as e:
            print(f"  ✗ {name} FAILED: {e}\n")
            logger.exception("Step '%s' failed", name)
            print("\nFix this step before proceeding. Stopping.")
            raise SystemExit(1)

    print("=" * 60)
    print("All tests passed — Bedrock is working correctly.")
    print("If the workflow still fails, the issue is in the graph/agent layer.")
    print("Run with LOG_LEVEL=DEBUG and check for '>>> run_planning called' etc.")
    print("=" * 60)
