# Epiphany
## Description
**Epiphany** - is a pre-engagement tool to perform assessment and basic analysis of the application, which would test from a DDoS perspective. 
- In the first stage, the tool performs link crawling, discovers POST and GET requests. 
- On the second stage: for each link, Epiphany performs a set of requests which count response time and detect pages that are most "heavy" and interesting for potential attackers. 
- Also, Epiphany performs heuristic discovery for cached pages. 

These functions allow a clear understanding of the attack surface to build high-quality test cases for the DDoS assessment and recommendations for remediation and control improvements.

## Disclaimer
> Epiphany should be used for authorized assessment and/or nonprofit educational purposes only. Any misuse of this software will not be the responsibility of the author or of any other collaborator. Use it at your own networks and/or with the network owner's permission.
## Installation
```pip3 install -r requirements.txt```

## Usage 
  ```python3 epiphany.py <host> <path_to_payload_lib>```

**File parameters:**
  * positional arguments:
    * ```host``` - Target Hosts
    * ```payload``` - Path to payload file for POST requests. Each line contains payload for the next parameter.

  * optional arguments:
    * ```-h, --help``` - show this help message and exit
    * ```-oC``` - Output result to console
    
## To do
- [x] Analysis of POST and GET requests **For now it's works as default option**
- [x] Adding output to XML **For now it's only one available output to file**
- [ ] Adding option to perform apart GET and POST analysis
- [ ] Adding optional output to JSON

## Authors
- [Cyberlands.io](https://cyberlands.io)
- [@excellencenatural](https://github.com/excellencenatural)

## License
Please follow the [LICENSE](LICENSE)