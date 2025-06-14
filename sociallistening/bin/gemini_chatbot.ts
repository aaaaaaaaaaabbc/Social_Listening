import 'source-map-support/register';
import { GeminiChatbotStack} from '../lib/gemini_chatbot-stack';
import * as cdk from 'aws-cdk-lib';

const app = new cdk.App();
new GeminiChatbotStack(app, 'GeminiChatbotStack', {
    modelId: 'gemini-2.5-pro-preview-06-05',

    env: {
        account : process.env.CDK_DEFAULT_ACCOUNT,
        region : process.env.CDK_DEFAULT_REGION || 'us-east-1'
    },
});

cdk.Tags.of(app).add('Project', 'Social Listening');
cdk.Tags.of(app).add('Environment','Dev')