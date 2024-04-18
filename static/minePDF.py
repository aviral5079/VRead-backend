import os
import sys
import json
import string
from dotenv import load_dotenv
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams, LTTextContainer, LTChar, LTTextBoxHorizontal
from pdfminer.converter import PDFPageAggregator
from langchain_community.llms import OpenAI
from langchain.docstore.document import Document
from langchain.chains.summarize import load_summarize_chain
from langchain.chains import MapReduceDocumentsChain, ReduceDocumentsChain
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from static.logger import log_info, log_error, log_critical, log_debug


class minePdfFile:
    def __init__(self):
        self.nodes = None
        self.edges = None

    def extract_and_convert(self, pdf_path):
        try:
            text_with_font_info_dict, formatted_strings = (
                self.extract_text_with_font_info(pdf_path)
            )
            log_info("Formatted Strings Created")
        except Exception as e:
            log_error("Failed to create formatted strings")
            log_debug(e)

        try:
            formatted_strings = [
                fs for fs in formatted_strings if fs.split("_")[-1].strip()
            ]

            combined_lines = {}
            for formatted_string in formatted_strings:
                try:
                    parts = formatted_string.split("_")
                    if len(parts) < 4:
                        continue
                    page_number, line_number, fontSize = map(int, parts[:-1])
                    line_text = parts[-1]

                    key = f"{page_number}_{line_number}_{fontSize}"
                    if key in combined_lines:
                        combined_lines[key] += (
                            " " + line_text
                        )  # Combine lines with space
                    else:
                        combined_lines[key] = line_text
                except Exception as e:
                    log_critical("Error In Combining Formatted Strings Loop")
                    log_debug(str(e))
                    continue
            # Use combined lines for further processing
            formatted_strings = [
                f"{key}_{value}" for key, value in combined_lines.items()
            ]
        except Exception as e:
            log_critical("Error Combining Formatted Strings")
            log_debug(f"Page Number : {page_number}, Line Number : {line_number}")

        try:
            self.nodes, self.edges = self.convert_formatted_strings_into_graph(
                formatted_strings
            )
            log_info("convert_formatted_strings_into_graph function called")
        except Exception as e:
            log_error("convert_formatted_strings_into_graph function not called")
            log_debug(e)

    def extract_and_convert_manual(self, pdf_path, page_numbers):
        try:
            text_with_font_info_dict, formatted_strings = (
                self.extract_text_with_font_info(pdf_path)
            )
            log_info("Formatted Strings Created")
        except Exception as e:
            log_error("Failed to create formatted strings")
            log_debug(e)

        try:
            formatted_strings = [
                fs for fs in formatted_strings if fs.split("_")[-1].strip()
            ]

            combined_lines = {}
            for formatted_string in formatted_strings:
                try:
                    parts = formatted_string.split("_")
                    if len(parts) < 4:
                        continue
                    page_number, line_number, fontSize = map(int, parts[:-1])
                    line_text = parts[-1]

                    key = f"{page_number}_{line_number}_{fontSize}"
                    if key in combined_lines:
                        combined_lines[key] += (
                            " " + line_text
                        )  # Combine lines with space
                    else:
                        combined_lines[key] = line_text
                except Exception as e:
                    log_critical("Error In Combining Formatted Strings Loop")
                    log_debug(str(e))
                    continue
            # Use combined lines for further processing
            formatted_strings = [
                f"{key}_{value}" for key, value in combined_lines.items()
            ]
        except Exception as e:
            log_critical("Error Combining Formatted Strings")
            log_debug(f"Page Number : {page_number}, Line Number : {line_number}")

        try:
            self.nodes, self.edges = self.create_graph_with_page_numbers(
                formatted_strings, page_numbers,
            )
            log_info("convert_formatted_strings_into_graph function called")
        except Exception as e:
            log_error("convert_formatted_strings_into_graph function not called")
            log_debug(e)
   
    def extract_text_with_font_info(self, pdf_path):
        text_with_font_info_dict = {}
        formatted_strings = []

        try:
            with open(pdf_path, "rb") as file:
                parser = PDFParser(file)
                document = PDFDocument(parser)
                rsrcmgr = PDFResourceManager()
                laparams = LAParams()
                device = PDFPageAggregator(rsrcmgr, laparams=laparams)
                interpreter = PDFPageInterpreter(rsrcmgr, device)

                for page_number, page in enumerate(
                    PDFPage.create_pages(document), start=1
                ):
                    interpreter.process_page(page)
                    layout = device.get_result()

                    for line_number, lt_obj in enumerate(layout, start=1):
                        try:
                            if isinstance(lt_obj, LTTextBoxHorizontal):
                                for i, text_line in enumerate(lt_obj):
                                    line_text = text_line.get_text().strip()
                                    for j, char in enumerate(text_line):
                                        # check for last character and compare font if not same, take last char font info
                                        if j % 4 == 0 and isinstance(char, LTChar):
                                            font_name = char.fontname[7:]
                                            font_size = int(char.size)
                                            key = f"{page_number}-{line_number}"
                                            text_with_font_info_dict[key] = {
                                                "text": line_text,
                                                "font_name": font_name,
                                                "font_size": font_size,
                                            }

                                            # Create formatted string and append to the array
                                            formatted_string = f"{page_number}_{line_number}_{font_size}_{line_text}"
                                            formatted_strings.append(formatted_string)

                                            break
                        except Exception as e:
                            log_debug(f"Error: {str(e)}")
                            log_debug(
                                f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name} Page Number : {page_number}, Line Number : {line_number}"
                            )
                            log_debug(
                                f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name} Page Content: {page}"
                            )

            log_info("PDF Miner Parsing Complete")

        except Exception as e:
            log_error(f"Error : {str(e)}")

        return text_with_font_info_dict, formatted_strings

    def convert_formatted_strings_into_graph(self, formatted_strings):
        try:
            stack = []
            edges_list = []  # to store parent-child relationships
            node_list = {}  # to store node information
            sequence_number = 1

            last_node = {"node_id": "root", "font_size": 249}
            stack.append(last_node)

            for formatted_string in formatted_strings:
                parts = formatted_string.split("_")
                if len(parts) < 4:
                    continue
                # print(f"Processing line: {formatted_string}")
                page_number, line_number, fontSize = map(int, parts[:-1])
                line_text = parts[-1]

                current_parent = stack[-1]

                if last_node["font_size"] != fontSize:
                    if fontSize < last_node["font_size"]:
                        stack.append(last_node)
                        current_parent = stack[-1]
                    elif fontSize > last_node["font_size"]:
                        while stack[-1]["font_size"] <= fontSize:
                            stack.pop()
                        if stack:
                            current_parent = stack[-1]
                        else:
                            current_parent = "root"

                # Create node_id using 'page_number'_'line_number'
                node_id = f"{page_number}_{line_number}"
                last_node = {"node_id": node_id, "font_size": fontSize}

                # Determine node type (title or text)
                if current_parent and current_parent["node_id"]:
                    node_type = "text"
                else:
                    node_type = "title"

                # Add node data to node_list
                node_list[node_id] = {
                    "data": {
                        "text": "" if node_type == "title" else line_text,
                        "title": line_text if node_type == "title" else "",
                        "font_size": fontSize,
                    }
                }

                # Add parent-child relationship to edges_list using node_ids
                parent_node_id = current_parent["node_id"]
                child_node_id = node_id
                edges_list.append(
                    {
                        "parent_id": parent_node_id,
                        "child_id": child_node_id,
                        "sequence_id": sequence_number,
                    }
                )
                sequence_number += 1

            # Update node_list based on edges_list
            for edge in edges_list:
                parent_id = edge["parent_id"]
                child_id = edge["child_id"]

                # If a node is a parent, update its type to "title"
                if parent_id in node_list and node_list[parent_id]["data"]["text"]:
                    node_list[parent_id]["data"]["title"] = node_list[parent_id][
                        "data"
                    ]["text"]
                    node_list[parent_id]["data"]["text"] = ""

            log_info("Stack Function Running Normal")

        except:
            log_error("Stack Function Error")

        return node_list, edges_list
    
    def create_graph_with_page_numbers(self, formatted_strings, page_numbers):
        try:
            edges_list = []  # to store parent-child relationships
            node_list = {}  # to store node information
            sequence_number = 1

            root_node_id = "0"
            root_node = {"node_id": root_node_id, "font_size": 0, "text": "PDF"}
            node_list[root_node_id] = {"data": root_node}

            # Sorting page numbers in ascending order
            page_numbers.sort()


            prev_page_number = 1
            # Loop through page numbers
            for page_number in page_numbers:
                # Create a new node for the page range
                page_node_id = f"Pages {prev_page_number}-{page_number - 1}"
                page_node = {
                    "node_id": page_node_id,
                    "font_size": 0,
                    "text": f"Pages {prev_page_number}-{page_number - 1}",
                    "title": "", 
                }
                node_list[page_node_id] = {"data": page_node}

                edges_list.append(
                    {
                        "parent_id": root_node_id,
                        "child_id": page_node_id,
                        "sequence_id": sequence_number,
                    }
                )
                sequence_number += 1

                prev_page_number = page_number
                
            prev_page_number = 1
            index = 0

            for user_page_number in page_numbers:
                page_node_id = f"Pages {prev_page_number}-{user_page_number - 1}"
                stack = []
                sequence_number = 1
                if(index >= len(formatted_strings)): break

                last_node = {"node_id": node_list[page_node_id]["data"]["node_id"], "font_size": 249}
                stack.append(last_node)
                while True:
                    parts = formatted_strings[index].split("_")
                    if len(parts) < 3:
                        continue
                    page_number = int(parts[0])
                    line_number = int(parts[1])
                    fontSize = int(parts[2])
                    line_text = "_".join(parts[3:])
                    if(page_number > user_page_number): break

                    current_parent = stack[-1]
                    if last_node["font_size"] != fontSize:
                        if fontSize < last_node["font_size"]:
                            stack.append(last_node)
                            current_parent = stack[-1]
                        elif fontSize > last_node["font_size"]:
                            while stack[-1]["font_size"] <= fontSize:
                                stack.pop()
                            if stack:
                                current_parent = stack[-1]
                            else:
                                current_parent = "page_node_id"
                    
                    # Create node_id using 'page_number'_'line_number'
                    node_id = f"{page_number}_{line_number}"
                    last_node = {"node_id": node_id, "font_size": fontSize}

                    # Determine node type (title or text)
                    if current_parent and current_parent["node_id"]:
                        node_type = "text"
                    else:
                        node_type = "title"

                    # Add node data to node_list
                    node_list[node_id] = {
                        "data": {
                            "text": "" if node_type == "title" else line_text,
                            "title": line_text if node_type == "title" else "",
                            "font_size": fontSize,
                        }
                    }

                    # Add parent-child relationship to edges_list using node_ids
                    parent_node_id = current_parent["node_id"]
                    child_node_id = node_id
                    edges_list.append(
                        {
                            "parent_id": parent_node_id,
                            "child_id": child_node_id,
                            "sequence_id": sequence_number,
                        }
                    )
                    sequence_number += 1
                    prev_page_number = user_page_number
                    index+=1

            log_info("Page Numbers Function Running Normal")
            
        except Exception as e:
            log_error(f"Page Numbers Function Error: {str(e)}")

        for edge in edges_list:
            parent_id = edge["parent_id"]
            child_id = edge["child_id"]
                
            # If a node is a parent, update its type to "title"
            if node_list[parent_id] and node_list[parent_id]["data"]["text"]:
                node_list[parent_id]["data"]["cursor"] = parent_id
                node_list[parent_id]["data"]["title"] = node_list[parent_id]["data"]["text"]
                node_list[parent_id]["data"]["text"] = ""
                
        filtered_edges = []
        for edge in edges_list:
            if edge["parent_id"] != edge["child_id"]:
                filtered_edges.append(edge)

        return node_list, filtered_edges

    def extract_lines_by_id_recursive(self, graph, edges, node_id, visited=None):
        if visited is None:
            visited = set()

        if node_id in visited:
            return ""

        visited.add(node_id)

        node_content = ""
        node = graph.get(node_id, None)

        if node:
            text_lines = node["data"].get("text", [])
            title_lines = node["data"].get("title", [])

            # Use "text" if it has data, otherwise use "title"
            lines = text_lines if text_lines else title_lines

            node_content = "".join(lines).replace("\n", "")

            # Traverse children recursively
            children_ids = [
                edge["child_id"] for edge in edges if edge["parent_id"] == node_id
            ]
            
            if not children_ids:
                return node_content
            
            for child_id in children_ids:
                if child_id in graph:
                    child_content = self.extract_lines_by_id_recursive(
                        graph, edges, child_id, visited
                    )
                    node_content += (
                        " " + child_content
                    )
        return node_content

    def extract_lines_by_id_and_children(self, node_id):
        
        if self.nodes is None or self.edges is None:
            log_error("Graph or edges not available.")
            return None
        
        visited = set()
        content = self.extract_lines_by_id_recursive(self.nodes, self.edges, node_id, visited)
        return content

    def get_node_summary(self, node_content):
        llm = ChatOpenAI(temperature=0)
        map_template = """The following is a set of documents
        {docs}
        Based on this list of docs, please identify the main themes 
        Helpful Answer:"""
        map_prompt = PromptTemplate.from_template(map_template)
        map_chain = LLMChain(llm=llm, prompt=map_prompt)

        reduce_template = """The following is set of summaries:
        {docs}
        Take these and distill it into a final, consolidated summary of the main themes. 
        Helpful Answer:"""
        reduce_prompt = PromptTemplate.from_template(reduce_template)

        reduce_chain = LLMChain(llm=llm, prompt=reduce_prompt)

        combine_documents_chain = StuffDocumentsChain(
            llm_chain=reduce_chain, document_variable_name="docs"
        )

        reduce_documents_chain = ReduceDocumentsChain(
            combine_documents_chain=combine_documents_chain,
            collapse_documents_chain=combine_documents_chain,
            token_max=4000,
        )

        map_reduce_chain = MapReduceDocumentsChain(
            llm_chain=map_chain,
            reduce_documents_chain=reduce_documents_chain,
            document_variable_name="docs",
            return_intermediate_steps=False,
        )

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts = text_splitter.split_text(node_content)

        docs = [Document(page_content=t) for t in texts]
        summary_output = map_reduce_chain.run(docs)

        return node_content, summary_output
