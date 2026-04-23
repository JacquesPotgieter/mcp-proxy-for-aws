# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Credential configuration tool for dynamic AWS profile switching."""

import logging
from typing import List, Optional

import boto3


logger = logging.getLogger(__name__)


def create_session(profile: Optional[str] = None) -> boto3.Session:
    """Create a boto3 session for the given profile.

    Args:
        profile: AWS profile name, or None for default credential chain.

    Raises:
        ValueError: If the profile does not exist or session creation fails.
    """
    try:
        return boto3.Session(profile_name=profile) if profile else boto3.Session()
    except Exception as e:
        raise ValueError(f'Failed to create session for profile {profile!r}: {e}') from e


def register_credential_tool(proxy, client_factory, args, service, region, metadata, timeout):
    """Register credential tools on the proxy.

    Args:
        proxy: The FastMCPProxy instance.
        client_factory: The AWSMCPProxyClientFactory instance.
        args: Parsed CLI arguments.
        service: AWS service name.
        region: Current AWS region.
        metadata: Metadata dict for MCP requests.
        timeout: httpx.Timeout for connections.
    """
    from mcp_proxy_for_aws.utils import create_transport_with_sigv4

    @proxy.tool(name='list_aws_profiles')
    async def list_aws_profiles() -> str:
        """List all available AWS profiles from ~/.aws/config and ~/.aws/credentials."""
        try:
            return list(boto3.Session().available_profiles)
        except Exception:
            logger.warning('Failed to list AWS profiles', exc_info=True)
            return 'Failed to list AWS profiles. Only default is available'

    @proxy.tool(name='use_aws_profile')
    async def use_aws_profile(profile: str | None = None) -> str:
        """Update AWS profile/credentials for the proxy connection.

        Disconnects from the downstream MCP server and reconnects with new credentials.
        Endpoint and region remain unchanged. Use list_aws_profiles to see available profiles.

        Args:
            profile: AWS profile name from ~/.aws/config. Omit to use default credential chain.
        """
        try:
            create_session(profile)
        except ValueError as e:
            return f'Error creating session with {profile}: {e}'

        try:
            new_transport = create_transport_with_sigv4(
                args.endpoint,
                service,
                region,
                metadata,
                timeout,
                profile,
                args.disable_telemetry,
            )
            await client_factory.reconfigure(new_transport)
        except Exception as e:
            logger.error('Failed to reconfigure: %s', e)
            return f'Error: Failed to reconfigure: {e}'

        return f'Switched to profile {profile or "default"}.'
