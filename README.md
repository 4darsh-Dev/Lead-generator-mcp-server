# Lead-generator-mcp-server
A mcp server for leads generator using google maps through playwright

## setup
1. create & activate the virtual env
```bash 
python -m venv myenv 
.\myenv\Scripts\Activate
```

2. install requirements.txt
```bash  
pip install -r requirements.txt
```

3. run script
```bash
python src/scraper.py --query "Fashion and Beauty in New Delhi" --max-results 3 --visible
```

