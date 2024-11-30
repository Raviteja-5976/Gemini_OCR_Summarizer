import os
import time
import google.generativeai as genai
import streamlit as st


apiKey = st.secrets["API_KEY"]
genai.configure(api_key=apiKey)

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

def wait_for_files_active(files):
  """Waits for the given files to be active.

  Some files uploaded to the Gemini API need to be processed before they can be
  used as prompt inputs. The status can be seen by querying the file's "state"
  field.

  This implementation uses a simple blocking polling loop. Production code
  should probably employ a more sophisticated approach.
  """
  print("Waiting for file processing...")
  for name in (file.name for file in files):
    file = genai.get_file(name)
    while file.state.name == "PROCESSING":
      print(".", end="", flush=True)
      time.sleep(10)
      file = genai.get_file(name)
    if file.state.name != "ACTIVE":
      raise Exception(f"File {file.name} failed to process")
  print("...all files ready")
  print()

# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

def main():
    st.title("Gemini OCR Summarizer")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    prompt_input = st.text_input("Enter your prompt", value="Summarize it")
    if st.button("Summarise"):
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with open(uploaded_file.name, "wb") as f:
                f.write(uploaded_file.getbuffer())
            # Upload the file to Gemini
            files = [upload_to_gemini(uploaded_file.name, mime_type="application/pdf")]
            wait_for_files_active(files)
            # Start the chat session with the user's prompt
            chat_session = model.start_chat(
                history=[
                    {
                        "role": "user",
                        "parts": [files[0], prompt_input],
                    },
                ]
            )
            # Pass the prompt_input as content to send_message()
            response = chat_session.send_message(prompt_input)
            st.write(response.text)
        else:
            st.warning("Please upload a file.")

if __name__ == "__main__":
    main()

# Remove or comment out the following lines, as they are now handled in the main function
# files = [
#   upload_to_gemini("pyhton functions 001.pdf", mime_type="application/pdf"),
# ]
# wait_for_files_active(files)
# chat_session = model.start_chat(
#     history=[
#         {
#             "role": "user",
#             "parts": [
#                 files[0],
#                 "Summarize it",
#             ],
#         },
#         {
#             "role": "model",
#             "parts": [
#                 "This document is a lesson on Python functions. It covers the following topics:\n\n* **Defining and Calling Functions:** Explains the syntax for creating functions using the `def` keyword, including parameters and the `return` statement. It shows how to call functions and the importance of defining functions before calling them.\n\n* **Advantages of Functions:** Highlights the benefits of using functions, such as code reusability, avoiding code duplication, and improved program organization.\n\n* **Call by Reference:** Explains that Python uses call by reference, meaning changes made to mutable objects within a function affect the original object, while changes to immutable objects do not.\n\n* **Types of Arguments:** Details different argument types:\n    * **Required Arguments:** Must be provided during function calls in the correct order.\n    * **Keyword Arguments:** Can be passed in any order using the parameter name.\n    * **Default Arguments:** Have a default value assigned in the function definition, so they don't need to be explicitly provided in every call.\n    * **Variable-Length Arguments:** Allows a function to accept a variable number of arguments using `*args`.\n\n* **Scope of Variables:** Explains the difference between global and local variables and their accessibility within functions.\n\nThe lesson uses numerous examples to illustrate each concept. It also includes examples demonstrating correct and incorrect usage of argument types and scope, highlighting potential errors.",
#             ],
#         },
#     ]
# )
# response = chat_session.send_message("INSERT_INPUT_HERE")
# print(response.text)