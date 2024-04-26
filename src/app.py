from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict
from static import (
    ingest,
    backend,
    mcqQuiz,
    trueFalseQuiz,
    multipleAnswerQuiz,
    oneWordQuiz,
)
from fastapi.responses import JSONResponse
from static.utils import Utils
import json
import importlib
from static.wordGlossary import WordCounter
from static.minePDF import minePdfFile
import os
import traceback
from static.logger import log_info, log_error, log_critical, log_debug
from fastapi.responses import FileResponse
from config import cfg
import sys
from static.RESPONSE_CODES import MCQ_JSON, MULTIPLEANSWER_JSON, TF_JSON, ONEWORD_JSON
from typing import List

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

word_counter = WordCounter()
pdf_processor_by_pdfid = {}
uploaded_pdfs: Dict[str, list] = {}


@app.post("/upload/pdf/")
async def upload_pdf(
    user_id: str = Query(..., description="User ID"),
    pdf_file: UploadFile = File(...),
):

    try:

        user_folder_path = f"{cfg.user_folder_path}/{user_id}"
        Utils.set_db_path(user_folder_path)

        if not os.path.exists(user_folder_path):
            os.makedirs(user_folder_path)

        pdf_file_id = f"{user_id}_{pdf_file.filename}"
        user_upload_folder = f"uploads/{user_id}"

        if not os.path.exists(user_upload_folder):
            os.makedirs(user_upload_folder)

        uploaded_file_path = f"{user_upload_folder}/{pdf_file_id}"
        with open(uploaded_file_path, "wb") as file:
            file.write(pdf_file.file.read())

        if user_id not in uploaded_pdfs:
            uploaded_pdfs[user_id] = []
        uploaded_pdfs[user_id].append(
            {
                "pdf_id": pdf_file_id,
                "file_path": uploaded_file_path,
            }
        )
        ingest.create_vector_database(user_id)
        
        pdf_processor = minePdfFile()

        importlib.reload(backend)
        pdf_processor.extract_and_convert(uploaded_file_path)

        pdf_processor_by_pdfid[pdf_file_id] = pdf_processor
        
        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory) 
        mindmap_folder = os.path.join(parent_directory, f"mindmaps/{user_id}")
        
        if not os.path.exists(mindmap_folder):
            os.makedirs(mindmap_folder)
    
        # Save mindmap node list
        node_list_file_path = os.path.join(mindmap_folder, f"{pdf_file_id}_nodes.json")
        with open(node_list_file_path, "w") as node_file:
            json.dump(pdf_processor.nodes, node_file)
            log_info(f"Node list saved for PDF {pdf_file_id}: {node_list_file_path}")

        # Save mindmap edges list
        edges_list_file_path = os.path.join(mindmap_folder, f"{pdf_file_id}_edges.json")
        with open(edges_list_file_path, "w") as edges_file:
            json.dump(pdf_processor.edges, edges_file)
            log_info(f"Edges list saved for PDF {pdf_file_id}: {edges_list_file_path}")

        return {
            "pdf_id": pdf_file_id,
            "file_path": uploaded_file_path,
            "uploaded_pdfs": uploaded_pdfs[user_id],
        }

    except HTTPException as e:
        log_error("Upload File and Mindmap Creation Failed")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )

        raise e

    except Exception as e:
        log_critical("Upload File and Mindmap Creation Failed")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/createManualMindmap")
async def upload_pdf(
    user_id: str = Query(..., description="User ID"),
    pdf_file_id: str = Query(..., description="Pdf File ID"),
    page_numbers: List[int] = Query(..., description="Array of page numbers")
):

    try:
        user_upload_folder = f"uploads/{user_id}"

        uploaded_file_path = f"{user_upload_folder}/{pdf_file_id}"
        ingest.create_vector_database(user_id)

        pdf_processor = pdf_processor_by_pdfid[pdf_file_id];
        importlib.reload(backend)
        pdf_processor.extract_and_convert_manual(uploaded_file_path, page_numbers)
        pdf_processor_by_pdfid[pdf_file_id] = pdf_processor
        
        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory) 
        mindmap_folder = os.path.join(parent_directory, f"mindmaps/{user_id}")
        
        if not os.path.exists(mindmap_folder):
            os.makedirs(mindmap_folder)
    
        # Save mindmap node list
        node_list_file_path = os.path.join(mindmap_folder, f"{pdf_file_id}_nodes.json")
        with open(node_list_file_path, "w") as node_file:
            json.dump(pdf_processor.nodes, node_file)
            log_info(f"Node list saved for PDF {pdf_file_id}: {node_list_file_path}")

        # Save mindmap edges list
        edges_list_file_path = os.path.join(mindmap_folder, f"{pdf_file_id}_edges.json")
        with open(edges_list_file_path, "w") as edges_file:
            json.dump(pdf_processor.edges, edges_file)
            log_info(f"Edges list saved for PDF {pdf_file_id}: {edges_list_file_path}")

        return {
            "pdf_id": pdf_file_id,
            "file_path": uploaded_file_path,
            "uploaded_pdfs": uploaded_pdfs[user_id],
        }

    except HTTPException as e:
        log_error("Upload File and Mindmap Creation Failed")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )

        raise e

    except Exception as e:
        log_critical("Upload File and Mindmap Creation Failed")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/getDocuments")
async def get_documents(
    user_id: str = Query(..., description="User ID"),
):
    try:
        current_directory = os.path.dirname(os.path.abspath(__file__))
        parent_directory = os.path.dirname(current_directory) 
        user_upload_folder = f"uploads/{user_id}"
        user_folder_path = os.path.join(parent_directory, user_upload_folder)

        if not os.path.exists(user_folder_path):
            return JSONResponse(content={"uploaded_files": {}}, status_code=200)

        files_list = os.listdir(user_folder_path)
        
        file_objects = {}

        for filename in files_list:
            
            file_path = os.path.join(user_folder_path, filename)
            file_objects[filename] = file_path;

        return JSONResponse(content={"uploaded_files": file_objects}, status_code=200)
    
    except HTTPException as e:
        log_error("Error retrieving documents")
        log_debug(
            f"Module Name: {__name__}, Function Name: {sys._getframe().f_code.co_name}, Error: {str(e)}"
        )
        raise e

    except Exception as e:
        log_critical("Error in getting documents")
        log_debug(
            f"Module Name: {__name__}, Function Name: {sys._getframe().f_code.co_name}, Error: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Error in getting documents")
    

@app.get("/queryResponse")
async def query_response(
    user_query: str = Query(..., description="User Query"),
):
    try:
        result = backend.qa.run(user_query)
        log_info(
            f"User query: {user_query}, Response: {result} - Module: {__name__}",
        )
        return JSONResponse(
            content={"query": str(user_query), "answer": str(result)},
        )
    except Exception as e:
        log_error("Query-Response Failed")
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/mindmapGraph")
async def mindmap_graph(
    user_id: str = Query(..., description="User ID"),
    pdf_file_id: str = Query(..., description="Pdf File ID"),
):
    try:
        
        nodes_file_path = os.path.join("mindmaps", user_id, f"{pdf_file_id}_nodes.json")
        edges_file_path = os.path.join("mindmaps", user_id, f"{pdf_file_id}_edges.json")

        if not os.path.exists(nodes_file_path) or not os.path.exists(edges_file_path):
            raise HTTPException(status_code=404, detail=f"Mindmap files not found for PDF {pdf_file_id}")

        with open(nodes_file_path, "r") as nodes_file:
            nodes = json.load(nodes_file)

        with open(edges_file_path, "r") as edges_file:
            edges = json.load(edges_file)

        log_info(
            f"Mindmap graph retrieved for PDF {pdf_file_id} - Module: {__name__}",
        )

        return JSONResponse(
            content={"nodes": nodes, "edges": edges},
            status_code=200
        )

    except HTTPException as e:
        log_error(f"Error retrieving mindmap graph for PDF {pdf_file_id}: {str(e)}")
        raise e

    except Exception as e:
        log_error(f"Error retrieving mindmap graph for PDF {pdf_file_id}: {str(e)}")
        log_debug(
            f"Module Name: {__name__}, Function Name: {sys._getframe().f_code.co_name}"
        )
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/get_node_summary")
async def get_node_summary(
    pdf_file_id: str = Query(..., description="PDF File ID"),
    node_id: str = Query(..., description="Node ID"),
):
    try:
        pdf_processor = pdf_processor_by_pdfid.get(pdf_file_id, None)
        if pdf_processor:
            node_content = pdf_processor.extract_lines_by_id_and_children(node_id)
            content, summary = pdf_processor.get_node_summary(node_content)
            log_info(
                f"Summary for node {node_id} retrieved successfully - Module: {__name__}",
            )
            return JSONResponse(
                content={"content": content, "summary": summary},
                status_code=200,
            )
        else:
            log_error(
                f"Mindmap graph not found for PDF {pdf_file_id} - Module: {__name__}",
            )
            return JSONResponse(
                content={"error": "Graph not found for the user"}, status_code=404
            )
    except HTTPException as e:
        log_error(
            f"Error retrieving summary for node {node_id} - Module: {__name__}",
        )
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )
        return JSONResponse(content={"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:
        log_error(
            f"Error retrieving summary for node {node_id}: - Module: {__name__}",
        )
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/topQuestions")
async def topQuestions(
    pdf_file_id: str = Query(..., description="PDF File ID"),
    node_id: str = Query(..., description="Node ID"),
    num_questions: str = Query(..., description="Number of Questions"),
    quiz_type: str = Query(..., description="Type of Quiz"),
):
    try:
        pdf_processor = pdf_processor_by_pdfid.get(pdf_file_id, None)
        if pdf_processor:
            node_content = pdf_processor.extract_lines_by_id_and_children(node_id)

            if quiz_type == "mcq" or quiz_type == "MCQ":
                response = mcqQuiz.quiz_chain.run(
                    text=node_content,
                    number=num_questions,
                    response_json=json.dumps(MCQ_JSON),
                )
            elif quiz_type == "tf" or quiz_type == "TF":
                response = trueFalseQuiz.quiz_chain.run(
                    text=node_content,
                    number=num_questions,
                    response_json=json.dumps(TF_JSON),
                )
            elif quiz_type == "oneword" or quiz_type == "ONEWORD":
                response = oneWordQuiz.quiz_chain.run(
                    text=node_content,
                    number=num_questions,
                    response_json=json.dumps(ONEWORD_JSON),
                )
            elif quiz_type == "maq" or quiz_type == "MAQ":
                response = multipleAnswerQuiz.quiz_chain.run(
                    text=node_content,
                    number=num_questions,
                    response_json=json.dumps(MULTIPLEANSWER_JSON),
                )
            else:
                return JSONResponse(
                    content={"error: Invalid quiz type entered"}, status_code=404
                )

            log_info(
                f"Questions generated for node {node_id} successfully - Module: {__name__}",
            )
            return JSONResponse(
                content={"quiz": response},
                status_code=200,
            )
        else:
            log_error(
                f"Mindmap graph not found for PDF {pdf_file_id} - Module: {__name__}",
            )
            return JSONResponse(
                content={"error": "Graph not found for the user"}, status_code=404
            )
    except HTTPException as e:
        log_error(
            f"Error generating questions for node {node_id} - Module: {__name__}",
        )
        return JSONResponse(content={"error": str(e.detail)}, status_code=e.status_code)
    except Exception as e:

        log_critical(
            f"Error generating questions for node {node_id}: {str(e)} - Module: {__name__}",
        )
        log_debug(
            f"Module Name : {__name__},Function Name : {sys._getframe().f_code.co_name}"
        )
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.get("/wordGlossary")
async def wordGlossary(
    pdf_file_id: str = Query(..., description="PDF File ID"),
    node_id: str = Query(..., description="Node ID"),
):
    try:
        pdf_processor = pdf_processor_by_pdfid.get(pdf_file_id, None)
        if pdf_processor:
            node_content = pdf_processor.extract_lines_by_id_and_children(node_id)
            result_json = word_counter.count_words_and_return_json(node_content)
            return JSONResponse(result_json)
    except Exception as e:
        log_error("Error counting words")
        log_debug(e)


@app.get("/download/pdf/")
async def download_pdf(
    file_path: str = Query(..., description="File Path"),
):
    try:
        # Ensure the file exists before serving
        if os.path.exists(file_path):
            log_info(
                f"User requested to download file: {file_path} - Module: {__name__}",
            )
            # Return the file as a response
            return FileResponse(file_path, media_type='application/pdf')
        else:
            log_error(
                f"File not found: {file_path} - Module: {__name__}",
            )
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        log_critical(
            f"Error downloading file: {str(e)} - Module: {__name__}",
        )
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
