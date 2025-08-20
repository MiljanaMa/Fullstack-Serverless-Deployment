export default {
  MAX_ATTACHMENT_SIZE: process.env.MAX_ATTACHMENT_SIZE || 5000000,
  apiGateway: {
    REGION: process.env.API_GATEWAY_REGION || 'eu-west-1',
    API_URL:
      process.env.API_URL ||
      'https://vnuqp5djfa.execute-api.eu-west-1.amazonaws.com/prod',
  },
  cognito: {
    REGION: process.env.COGNITO_REGION || 'eu-west-1',
    USER_POOL_ID: process.env.COGNITO_USER_POOL_ID || 'eu-west-1_6pfNYzm8q',
    APP_CLIENT_ID:
      process.env.COGNITO_APP_CLIENT_ID || '7bldv2hshvji3vnctr6gs8rjd6',
    IDENTITY_POOL_ID:
      process.env.COGNITO_IDENTITY_POOL_ID ||
      'us-east-1:7a11df8f-43ae-4e5e-a787-1956fc01a2a8',
  },
};
