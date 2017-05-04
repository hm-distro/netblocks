#
# Copyright 2017 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module retrieves the DNS entries recursively as per the below link.

https://cloud.google.com/compute/docs/faq#where_can_i_find_short_product_name_ip_ranges
"""

import json
import logging

from google.appengine.api import urlfetch
from googleapiclient import discovery
from oauth2client import client


CREDENTIALS = client.GoogleCredentials.get_application_default()
SERVICE = discovery.build("compute", "beta", credentials=CREDENTIALS)
urlfetch.set_default_fetch_deadline(60)

DNS_URL = "https://dns.google.com/resolve?name=%s&type=TXT"
INITIAL_NETBLOCK_DNS = "_cloud-netblocks.googleusercontent.com"


class NetBlockRetrievalException(Exception):
    """
    This exception is a wrapper exception from this module.
    
    This exception is thrown for any non successful operation in getting
    the DNS entries
    """
    pass


class NetBlocks(object):
    """
    This class retrieves the DNS entries recursively.

    """

    def _fetch_json_(self, url):
        """
        Fetch the data from the url and extract the relevant json payload.
      
        Retrieves data from the url and extracts the relevant json payload.
        If there is an issue, return error message and the code.
      
        Args:
          url: The URL to fetch the json payload
      
        Returns:
          A tuple with either a (json payload, 200) or (error message, status code)
      
        Raises:
          Exception: Any non 200 message raises this Exception
        """

        result = urlfetch.fetch(url, validate_certificate=True)
        if result.status_code == 200:  # OK.no issues
            try:
                structured_dictionary = json.loads(result.content)
            except ValueError, e:
                raise Exception("Invalid json returned from %s. %s " % (url, e.message))
            # Valid json. Proceed with extract.
            return structured_dictionary["Answer"][0]["data"]
        else:
            logging.error(result.status_code)
            raise Exception("Error in fetching %s.Code %d."
                            % (url, result.status_code))

    def fetch(self):
        """
        The main entry point to this class.
    
        This method makes a call to the DNS servers, retrieves the json payload.
        extracts the ip addresses, and inserts them into a set that is returned.
        The set contains strings like the below
        ip4:146.148.2.0/23
        ip6:2600:1900::/35
    
        Returns:
          A set of cidr blocks
    
        Raises:
          NetBlockRetrievalException: raised if any issue in fetch
        """
        logging.info("netblocks refresh called")
        cidr_blocks = set()

        # Catch any exceptions and fail even if one call has an issue.
        # The All or fail is to is to prevent partial info from being returned.
        try:
            # Get the list of dns name servers to lookup
            result = None
            result = self._fetch_json_(DNS_URL % INITIAL_NETBLOCK_DNS)
            netblock_dns = []
            if result is not None:
                include_list = result.split(" ")
                for include in include_list:
                    if include.startswith("include:"):
                        netblock_dns.append(include.split("include:")[1])

                # Get the CIDR blocks from each of the dns name servers
                for netblock_dns_entry in netblock_dns:
                    result = None  # reset it
                    result = self._fetch_json_(DNS_URL % netblock_dns_entry)
                    if result is not None:
                        items = result.split(" ")
                        for item in items:
                            if item.startswith("ip"):
                                cidr_blocks.add(str(item))
                return cidr_blocks
        except Exception as e:
            raise NetBlockRetrievalException(e.message)