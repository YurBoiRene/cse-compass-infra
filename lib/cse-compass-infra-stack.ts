import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as sns from 'aws-cdk-lib/aws-sns'
import { EmailSubscription } from 'aws-cdk-lib/aws-sns-subscriptions'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { DynamoEventSource, SnsDlq } from 'aws-cdk-lib/aws-lambda-event-sources'
import path = require('path');
import { Duration } from 'aws-cdk-lib';

export class CseCompassInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const tokensTable = new dynamodb.Table(this, 'tokens', {
      partitionKey: { name: 'token', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      timeToLiveAttribute: 'expires_at',
    });

    const pollTable = new dynamodb.Table(this, 'polls', {
      partitionKey: { name: 'class', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'type-email', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      stream: dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
    });

    const statisticsTable = new dynamodb.Table(this, 'pollStatistics', {
      partitionKey: { name: 'type', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'class', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
    });

    const pollStreamErrorTopic = new sns.Topic(this, 'PollStreamErrorTopic', {
      displayName: 'Poll stream error topic',
    });


    pollStreamErrorTopic.addSubscription(new EmailSubscription("anderslennon@gmail.com"));
    const pollChangedSourceProps = new DynamoEventSource(pollTable, {
      startingPosition: lambda.StartingPosition.TRIM_HORIZON,
      batchSize: 5,
      bisectBatchOnError: true,
      maxBatchingWindow: Duration.seconds(10),
      onFailure: new SnsDlq(pollStreamErrorTopic),
      retryAttempts: 2,
    });

    const emailIndexProps: dynamodb.GlobalSecondaryIndexProps = {
      indexName: 'email-expires_at-index',
      partitionKey: {
        name: 'email',
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: 'expires_at',
        type: dynamodb.AttributeType.NUMBER,
      },
    
      nonKeyAttributes: ['used'],
      projectionType: dynamodb.ProjectionType.INCLUDE,
    };
    tokensTable.addGlobalSecondaryIndex(emailIndexProps);

    
    const sendTokenHandler = new lambda.Function(this, 'SendToken', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../resources/sendToken')),
      handler: 'sendToken.lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        TOKEN_TABLE_NAME: tokensTable.tableName,
        EMAIL_INDEX_NAME: emailIndexProps.indexName,
      }
    });
    tokensTable.grantReadWriteData(sendTokenHandler);
    
    
    const submitPollHandler = new lambda.Function(this, 'SubmitPoll', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../resources/submitPoll')),
      handler: 'submitPoll.lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        TOKEN_TABLE_NAME: tokensTable.tableName,
        POLL_TABLE_NAME: pollTable.tableName,
      },
    });
    tokensTable.grantReadWriteData(submitPollHandler);
    pollTable.grantReadWriteData(submitPollHandler);

    const pollChangedHandler = new lambda.Function(this, 'PollChanged', {
      code: lambda.Code.fromAsset(path.join(__dirname, '../resources/pollChanged')),
      handler: 'pollChanged.lambda_handler',
      runtime: lambda.Runtime.PYTHON_3_9,
      environment: {
        STATISTICS_TABLE_NAME: statisticsTable.tableName,
      },
    });
    pollChangedHandler.addEventSource(pollChangedSourceProps);
    statisticsTable.grantReadWriteData(pollChangedHandler);


    
  }
}
