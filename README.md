# CSE Compass Infra

AWS infrastructure for CSE Compass website written using the [AWS CDK](https://aws.amazon.com/cdk/).

## Useful commands

* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template

## Testing Lambda Codes

```bash
pip install -r requirements.txt
pytest --cov=resources/lambda/src resources/lambda/
```

No testing for infrastructure.
