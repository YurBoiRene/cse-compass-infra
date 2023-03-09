#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CseCompassInfraStack } from '../lib/cse-compass-infra-stack';

const app = new cdk.App();
new CseCompassInfraStack(app, 'CseCompassInfraStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION 
}});