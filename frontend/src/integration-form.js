import { useState } from 'react';
import {
    Box,
    Autocomplete,
    TextField,
    Container,
    Paper,
    Typography,
    Divider,
} from '@mui/material';
import { AirtableIntegration } from './integrations/airtable';
import { NotionIntegration } from './integrations/notion';
import { HubspotIntegration } from './integrations/hubspot';
import { DataForm } from './data-form';

const integrationMapping = {
    'Notion': NotionIntegration,
    'Airtable': AirtableIntegration,
    'HubSpot': HubspotIntegration,
};

export const IntegrationForm = () => {
    const [integrationParams, setIntegrationParams] = useState({});
    const [user, setUser] = useState('TestUser');
    const [org, setOrg] = useState('TestOrg');
    const [currType, setCurrType] = useState(null);
    const CurrIntegration = integrationMapping[currType];

  return (
    <Container maxWidth="sm" sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
            <Typography variant="h5" component="h1" gutterBottom align="center">
                Connect an Integration
            </Typography>
            <Divider sx={{ mb: 3 }} />
            <Box display='flex' flexDirection='column' alignItems='center'>
                <TextField
                    label="User"
                    value={user}
                    onChange={(e) => setUser(e.target.value)}
                    sx={{ mb: 2, width: '100%' }}
                />
                <TextField
                    label="Organization"
                    value={org}
                    onChange={(e) => setOrg(e.target.value)}
                    sx={{ mb: 2, width: '100%' }}
                />
                <Autocomplete
                    id="integration-type"
                    options={Object.keys(integrationMapping)}
                    sx={{ width: '100%' }}
                    renderInput={(params) => <TextField {...params} label="Integration Type" />}
                    onChange={(e, value) => {
                        setCurrType(value);
                        setIntegrationParams({}); // Clear previous integration data
                    }}
                    value={currType}
                />
            </Box>
            
            {currType && 
            <Box>
                <CurrIntegration user={user} org={org} integrationParams={integrationParams} setIntegrationParams={setIntegrationParams} />
            </Box>
            }
            
            {integrationParams?.credentials && 
            <Box>
                <DataForm integrationType={integrationParams?.type} credentials={integrationParams?.credentials} />
            </Box>
            }
        </Paper>
    </Container>
  );
}