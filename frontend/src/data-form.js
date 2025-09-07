import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Typography,
    Paper,
    List,
    ListItem,
    ListItemText,
    Divider,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'Hubspot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const endpoint = endpointMapping[integrationType];

    const handleLoad = async () => {
        try {
            setLoading(true);
            setError(null);
            
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            
            // const url = `http://localhost:8000/integrations/${endpoint}/load`;

            const url = integrationType === 'Hubspot' 
                ? `http://localhost:8000/integrations/${endpoint}/get_hubspot_items`
                : `http://localhost:8000/integrations/${endpoint}/load`;
                
            console.log('Making request to:', url);
            console.log('With credentials:', credentials);
            
            const response = await axios.post(url, formData);
            const data = response.data;
            
            console.log('Received data:', data);
            setLoadedData(data);
        } catch (e) {
            console.error('Error loading data:', e);
            setError(e?.response?.data?.detail || e.message);
            alert(e?.response?.data?.detail || e.message);
        } finally {
            setLoading(false);
        }
    }

    const renderLoadedData = () => {
        if (!loadedData) return null;

        let itemsToDisplay = [];
        let totalCount = 0;
        let message = '';

        if (loadedData.items && Array.isArray(loadedData.items)) {
            itemsToDisplay = loadedData.items;
            totalCount = loadedData.total_items || itemsToDisplay.length;
            message = loadedData.message || '';
        } else if (Array.isArray(loadedData)) {
            itemsToDisplay = loadedData;
            totalCount = itemsToDisplay.length;
        }

        if (itemsToDisplay.length === 0) {
            return (
                <Paper sx={{ p: 2, mt: 2 }}>
                    <Typography>No data found</Typography>
                    {message && <Typography variant="body2" sx={{ mt: 1 }}>{message}</Typography>}
                </Paper>
            );
        }

        return (
            <Paper sx={{ p: 2, mt: 2, maxHeight: 400, overflow: 'auto' }}>
                <Typography variant="h6" gutterBottom>
                    Loaded {totalCount} items from {integrationType}
                </Typography>
                {message && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {message}
                    </Typography>
                )}
                <List>
                    {itemsToDisplay.map((item, index) => (
                        <div key={item.id || index}>
                            <ListItem>
                                <ListItemText
                                    primary={`${item.name || 'Unnamed'} (${item.type || 'Unknown type'})`}
                                    secondary={
                                        <div>
                                            <Typography variant="body2">ID: {item.id}</Typography>
                                            {item.creation_time && (
                                                <Typography variant="body2">
                                                    Created: {new Date(item.creation_time).toLocaleDateString()}
                                                </Typography>
                                            )}
                                            {item.last_modified_time && (
                                                <Typography variant="body2">
                                                    Modified: {new Date(item.last_modified_time).toLocaleDateString()}
                                                </Typography>
                                            )}
                                        </div>
                                    }
                                />
                            </ListItem>
                            {index < itemsToDisplay.length - 1 && <Divider />}
                        </div>
                    ))}
                </List>
            </Paper>
        );
    };

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                    disabled={loading}
                >
                    {loading ? 'Loading Data...' : 'Load Data'}
                </Button>
                
                <Button
                    onClick={() => {
                        setLoadedData(null);
                        setError(null);
                    }}
                    sx={{mt: 1}}
                    variant='outlined'
                    disabled={!loadedData && !error}
                >
                    Clear Data
                </Button>

                {error && (
                    <Paper sx={{ p: 2, mt: 2, bgcolor: 'error.light' }}>
                        <Typography color="error">Error: {error}</Typography>
                    </Paper>
                )}

                {renderLoadedData()}
            </Box>
        </Box>
    );
}