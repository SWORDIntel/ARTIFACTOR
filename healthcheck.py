#!/usr/bin/env python3
"""
Docker health check script for Etherscan API
DOCKER-AGENT Implementation
"""

import sys
import requests
import json

def main():
    """Perform health check"""
    try:
        # Check if the API is responding
        response = requests.get('http://localhost:8080/health', timeout=5)

        if response.status_code == 200:
            data = response.json()

            # Check if the API status is healthy
            if data.get('status') == 'healthy':
                print("✅ Health check passed")
                sys.exit(0)
            else:
                print(f"⚠️ API status: {data.get('status')}")
                sys.exit(1)
        else:
            print(f"❌ HTTP {response.status_code}")
            sys.exit(1)

    except requests.exceptions.ConnectRefusedError:
        print("❌ Connection refused")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()