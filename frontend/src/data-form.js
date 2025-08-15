import { useState } from 'react';
import {
    Box,
    Button,
    Paper,
    List,
    ListItem,
    ListItemText,
    Typography,
    CircularProgress,
    Divider,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        setIsLoading(true);
        setLoadedData(null);
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            setLoadedData(response.data);
        } catch (e) {
            alert(e?.response?.data?.detail);
        } finally {
            setIsLoading(false);
        }
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%' sx={{ mt: 2 }}>
                <Button
                    onClick={handleLoad}
                    variant='contained'
                    disabled={isLoading}
                >
                    {isLoading ? <CircularProgress size={24} color="inherit" /> : `Load Data From ${integrationType}`}
                </Button>

                {loadedData && (
                    <Paper variant="outlined" sx={{ mt: 2, width: '100%' }}>
                        <List dense>
                            <ListItem>
                                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                                    Fetched Contacts
                                </Typography>
                            </ListItem>
                            <Divider />
                            {loadedData.length > 0 ? (
                                loadedData.map((item) => (
                                    <ListItem key={item.id}>
                                        <ListItemText primary={item.name} secondary={`ID: ${item.id}`} />
                                    </ListItem>
                                ))
                            ) : (
                                <ListItem>
                                    <ListItemText primary="No contacts found." />
                                </ListItem>
                            )}
                        </List>
                    </Paper>
                )}
            </Box>
        </Box>
    );
}