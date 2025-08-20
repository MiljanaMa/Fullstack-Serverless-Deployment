import React from 'react';
import ReactDOM from 'react-dom';
import { BrowserRouter as Router } from 'react-router-dom';
import './index.css';
import App from './App';
import registerServiceWorker from './registerServiceWorker';
import Amplify from '@aws-amplify/core';
import config from './config';

import 'bootstrap/dist/css/bootstrap.css';
import Auth from '@aws-amplify/auth';

Amplify.configure({
  Auth: {
    mandatorySignIn: true,
    region: config.cognito.REGION,
    userPoolId: config.cognito.USER_POOL_ID,
    identityPoolId: config.cognito.IDENTITY_POOL_ID,
    userPoolWebClientId: config.cognito.APP_CLIENT_ID,
  },
  API: {
    endpoints: [
      {
        name: 'goals',
        endpoint: config.apiGateway.API_URL,
        region: config.apiGateway.REGION,
        custom_header: async () => {
          try {
            const currentUser = await Auth.currentAuthenticatedUser();

            if (currentUser) {
              const session = await Auth.currentSession();
              const idToken = session.getIdToken().getJwtToken();

              return {
                Authorization: `Bearer ${idToken}`,
              };
            } else {
              console.error('User is not authenticated');
              return {};
            }
          } catch (error) {
            console.error('Error getting ID token', error);
            return {};
          }
        },
      },
    ],
  },
});

ReactDOM.render(
  <Router>
    <App />
  </Router>,
  document.getElementById('root')
);
registerServiceWorker();
