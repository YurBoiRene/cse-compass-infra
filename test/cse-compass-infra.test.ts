import * as cdk from 'aws-cdk-lib';
import { Template, Match } from 'aws-cdk-lib/assertions';
import * as CseCompassInfra from '../lib/cse-compass-infra-stack';


test('Poll Table Created', () => {
  const app = new cdk.App();
    // WHEN
  const stack = new CseCompassInfra.CseCompassInfraStack(app, 'MyTestStack');
    // THEN
  const template = Template.fromStack(stack);
  
  template.hasResourceProperties('AWS::DynamoDB::Table', {
    id: Match.stringLikeRegexp('polls'),
  })

  

//   template.hasResourceProperties('AWS::SQS::Queue', {
//     VisibilityTimeout: 300
//   });
});
