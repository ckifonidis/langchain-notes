To get the credentials for the `GoogleSearchAPIWrapper` in LangChain, you need to obtain two key pieces of information:

1. **Google API Key (`GOOGLE_API_KEY`)**: This is your authentication key for accessing Google APIs.
2. **Custom Search Engine ID (`GOOGLE_CSE_ID`)**: This is the unique identifier for your custom search engine, which allows you to search the web programmatically.

Below are the steps to obtain these credentials:

---

### 1. **Obtain the Google API Key (`GOOGLE_API_KEY`)**
You can create a Google API Key by following these steps:

1. **Go to the Google Cloud Console**:
   - Visit [Google Cloud Console](https://console.cloud.google.com/apis/credentials).
   - If you don’t already have a Google Cloud project, create one by clicking "Create Project" and following the prompts.

2. **Enable the Custom Search API**:
   - In the Google Cloud Console, navigate to the "APIs & Services" dashboard.
   - Click on "Enable APIs and Services."
   - Search for "Custom Search API" and enable it for your project.

3. **Create an API Key**:
   - Go to the "Credentials" section.
   - Click "Create Credentials" and select "API key."
   - Your API key will be generated and displayed. Copy this key and save it for later use.

---

### 2. **Obtain the Custom Search Engine ID (`GOOGLE_CSE_ID`)**
To create a Custom Search Engine ID, follow these steps:

1. **Go to the Programmable Search Engine Control Panel**:
   - Visit [Programmable Search Engine](https://programmablesearchengine.google.com/controlpanel/create).

2. **Create a New Search Engine**:
   - Name your search engine.
   - In the "Sites to Search" section, you can either specify specific websites or choose "Search the entire web."
   - Click "Create" to finish setting up the search engine.

3. **Get the Search Engine ID**:
   - After creating the search engine, you will be redirected to the control panel.
   - In the "Overview" section, you will find the "Search Engine ID." Copy this ID and save it for later use.

---

### 3. **Set Up Environment Variables**
Once you have both the `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`, you need to set them as environment variables in your Python code. This ensures that your credentials are securely passed to the `GoogleSearchAPIWrapper`.

```python
import os

# Set your Google API Key and Custom Search Engine ID
os.environ["GOOGLE_API_KEY"] = "your_api_key_here"
os.environ["GOOGLE_CSE_ID"] = "your_cse_id_here"
```

---

### 4. **Install Required Libraries**
To use the `GoogleSearchAPIWrapper` in LangChain, you need to install the `langchain_google_community` library. You can do this using pip:

```bash
pip install langchain_google_community
```

---

### 5. **Initialize the GoogleSearchAPIWrapper**
Once the credentials are set up, you can initialize the `GoogleSearchAPIWrapper` in your code:

```python
from langchain_google_community import GoogleSearchAPIWrapper

# Initialize the GoogleSearchAPIWrapper
search = GoogleSearchAPIWrapper()
```

---

### Summary of Steps
1. **Get `GOOGLE_API_KEY`**: Create an API key in the Google Cloud Console.
2. **Get `GOOGLE_CSE_ID`**: Create a custom search engine in the Programmable Search Engine Control Panel.
3. **Set Environment Variables**: Use `os.environ` to set the API key and CSE ID in your code.
4. **Install Required Libraries**: Install `langchain_google_community`.
5. **Initialize the Wrapper**: Use the `GoogleSearchAPIWrapper` to perform searches.

By following these steps, you will have the necessary credentials to use the `GoogleSearchAPIWrapper` in LangChain. For more details, you can refer to the official documentation or the examples provided in the search results, such as .