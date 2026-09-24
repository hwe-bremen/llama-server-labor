# Models.ini Configuration Summary

## Overview
This configuration file sets up model presets for llama.cpp's `--models-preset` feature, specifically optimized for Mellum models with reasoning capabilities.

## Global Settings
- **Context Size**: 32768 tokens
- **GPU Layers**: 99
- **Jinja Template**: Enabled

## Mellum Models

### Mellum Q6 (12B)
- **Repository**: JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q6_K:Q6_K
- **Temperature**: 0.2
- **Top-p**: 0.95
- **Reasoning**: DeepSeek format
- **Reasoning Budget**: 8192 tokens

### Mellum Q4 (12B)
- **Repository**: JetBrains/Mellum2-12B-A2.5B-Thinking-GGUF-Q4_K_M:Q4_K_M
- **Temperature**: 0.2
- **Top-p**: 0.95
- **Reasoning**: DeepSeek format
- **Reasoning Budget**: 8192 tokens

## Other Models

### Qwen3.6 27B
- **Repository**: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL
- **Temperature**: 0.6
- **Top-p**: 0.95
- **Top-k**: 20
- **Min-p**: 0.0

### Gemma 4 26B
- **Repository**: unsloth/gemma-4-26B-A4B-it-GGUF:Q4_K_XL
- **Temperature**: 1.0
- **Top-p**: 0.95
- **Top-k**: 64

### Apertus 8B
- **Repository**: jondale/Apertus-8B-Instruct-2509-GGUF:Q4_K_M
- **Temperature**: 0.8
- **Top-p**: 0.9

## Notes
- Reasoning capabilities are enabled for Mellum models with a budget of 8192 tokens
- Lower temperatures (0.2) are used for Mellum models to ensure stable tool calls and reproducible code output
- The configuration is optimized for MCP-Tool-Workflows that fill context quickly
- A warning is included about potential issues with certain GGUF uploads causing server crashes