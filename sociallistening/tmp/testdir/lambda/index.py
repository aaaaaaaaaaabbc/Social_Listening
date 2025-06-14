
import os
import re
import json
from google import genai

#グローバル変数としてクライアントを初期化
client = None

#モデルID
MODEL_ID = os.environ.get("MODEL_ID","gemini-2.5-pro-preview-06-05")
#APIキーを取得
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def chat_response(event,context):
    try:
        global client
        client = genai.Client(api_key = GEMINI_API_KEY)

        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        #リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']

        print("Processing message:", message)
        print("Using model:", MODEL_ID)

        response = client.models.generate_content(
            model = MODEL_ID,
            contents = message
        )
        

        #レスポンスを解析
        print("Response received from model:",response.text)

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
                "response": response.text,
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

