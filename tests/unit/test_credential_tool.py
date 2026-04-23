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

"""Tests for credential_tool module."""

import pytest
from mcp_proxy_for_aws.credential_tool import create_session
from unittest.mock import MagicMock, patch


class TestCreateSession:
    """Tests for create_session."""

    @patch('mcp_proxy_for_aws.credential_tool.boto3.Session')
    def test_with_profile(self, mock_session_cls):
        """Test session creation with explicit profile."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        result = create_session('prod')
        mock_session_cls.assert_called_once_with(profile_name='prod')
        assert result is mock_session

    @patch('mcp_proxy_for_aws.credential_tool.boto3.Session')
    def test_without_profile(self, mock_session_cls):
        """Test session creation with default credential chain."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        result = create_session(None)
        mock_session_cls.assert_called_once_with()
        assert result is mock_session

    @patch('mcp_proxy_for_aws.credential_tool.boto3.Session')
    def test_invalid_profile_raises(self, mock_session_cls):
        """Test that invalid profile raises ValueError."""
        mock_session_cls.side_effect = Exception('profile not found')

        with pytest.raises(ValueError, match='Failed to create session'):
            create_session('nonexistent')
