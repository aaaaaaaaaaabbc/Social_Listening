import gradio as gr
import os
import re
import boto3
import json
from botocore.exceptions import ClientError

def extract_region_from_arn(arn):
    match = re.search('arn:aws:lambda:([^:]+):',arn)
    if match:
        return match.group(1)
    return "us-east-1" #デフォルト値

#グローバル変数としてクライアントを初期化
bedrock_client = None

#モデルID
MODEL_ID = os.environ.get("MODEL_ID","us.amazon.nova-lite-v1:0")

def chat_response(event,context):
    try:
        global bedrock_client
        if bedrock_client is None:
            region = extract_region_from_arn(context.invoked_function_arn)
            bedrock_client = boto3.client('bedrock-runtime',region_name = region)
            print(f"Initialized Bedrock client in region: {region}")
        
        print("Received event:", json.dumps(event))

        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        #リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory',[])

        print("Processing message:", message)
        print("Using model:", MODEL_ID)

        #会話履歴を使用
        messages = conversation_history.copy()

        #ユーザーメッセージを追加
        messages.append({
            "role": "user",
            "content": message
        })

        #Nova Liteモデル用のリクエストペイロードを構築
        #会話履歴を含める
        bedrock_messages = []
        for msg in messages:
            if msg["role"] == "user":
                bedrock_messages.append({
                    "role": "user",
                    "content": [{"text":msg["content"]}]
                })
            elif msg["role"] == "assistant":
                bedrock_messages.append({
                    "role": "assistant",
                    "content": [{"text": msg["content"]}]
                })
        
        # invoke_model用のリクエストペイロード
        request_payload = {
            "message": bedrock_messages,
            "inferenceConfig": {
                "maxTokens": 512,
                "stopSequences": [],
                "temperature": 0.7,
                "topP": 0.9
            }
        }

        print("Calling Bedrock invoke_model API with payload:", json.dumps(request_payload))

        # Invoke_model APIを呼び出し
        response = bedrock_client.invoke_model(
            modelID = MODEL_ID,
            body = json.dumps(request_payload),
            contentType = "application/json"
        )

        #レスポンスを解析
        response_body = json.loads(response['body'].read())
        print("Bedrock response:", json.dumps(response_body, default = str))

        #応答の検証
        if not response_body.get('output') or not response_body['output'].get('message') or not response_body['output']['message'].get('content'):
            raise Exception("No response content from the model")
        
        #アシスタントの応答を取得
        assistant_response = response_body['output']['message']['content'][0]['text']


        #アシスタントの応答を会話履歴に追加
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })

        #成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }
    except Exception as error:
        print("Error:", str(error))

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success":False,
                "error":str(error)
            })
        }


def greet(name):
    return "Hello " + name + "!"

# インターフェースの作成
# fn: 実行する関数
# inputs: 入力のコンポーネントの種類
# outputs: 出力のコンポーネントの種類
demo = gr.Interface(fn=greet, inputs="text", outputs="text")

# Web UIの起動
demo.launch()