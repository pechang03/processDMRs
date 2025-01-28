import React, { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../config';
import {
Box,
Select,
MenuItem,
TextField,
Button,
Typography,
Paper,
FormControl,
InputLabel,
Container,
CircularProgress,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const LLMAnalysisView = ({ selectedTimepoint: initialTimepoint }) => {
// Initialize state for error handling and data
const [error, setError] = useState(null);
const [timepoints, setTimepoints] = useState([]);
const [selectedPrompt, setSelectedPrompt] = useState('');
const [prompts, setPrompts] = useState([]);
const [messages, setMessages] = useState([]);
const [inputMessage, setInputMessage] = useState('');
const [selectedTimepoint, setSelectedTimepoint] = useState('');
const [currentTimepoint, setCurrentTimepoint] = useState(null);
const [isLoading, setIsLoading] = useState(false);
const [selectedModel, setSelectedModel] = useState('');
const [providers, setProviders] = useState([]);
const [models, setModels] = useState({});
const [modelsLoaded, setModelsLoaded] = useState(false);
const messagesEndRef = useRef(null);

useEffect(() => {
    // Fetch timepoints on component mount
    const fetchTimepoints = async () => {
        try {
            console.log('Fetching timepoints...'); 
            const response = await fetch(`${API_BASE_URL}/timepoints`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Fetched timepoints:', data);
            
            if (Array.isArray(data) && data.length > 0) {
                console.log(`Found ${data.length} timepoints. First timepoint:`, data[0]);
                setTimepoints(data);
                // Only set selectedTimepoint if none is set and no initialTimepoint was provided
                if (!selectedTimepoint && !initialTimepoint) {
                    setSelectedTimepoint(String(data[0].id));
                }
            } else {
                console.warn('No timepoints found in response');
                setError('No timepoints available. Please check the data source.');
            }
        } catch (error) {
            console.error('Error fetching timepoints:', error);
            setError('Failed to load timepoints. Please try refreshing the page.');
        }
    };
    
    fetchTimepoints();
}, []); // Only run on mount

useEffect(() => {
    // Fetch available prompts from backend
    const fetchPrompts = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/llm/prompts`);
        const data = await response.json();
        console.log('Fetched prompts:', data);
        
        // Convert prompts object to array if needed
        const promptsArray = Array.isArray(data.prompts) 
            ? data.prompts 
            : data.prompts 
                ? Object.values(data.prompts)
                : [];
        
        setPrompts(promptsArray);
        if (promptsArray.length > 0) {
            setSelectedPrompt(promptsArray[0].id);
        }
    } catch (error) {
        console.error('Error fetching prompts:', error);
        setError('Failed to load prompts. Please try refreshing the page.');
        setPrompts([]); // Set empty array on error
    }
    };
    fetchPrompts();
}, []);


// Update selectedTimepoint when prop changes
useEffect(() => {
    if (initialTimepoint && timepoints.length > 0) {
        const exists = timepoints.some(t => String(t.id) === String(initialTimepoint));
        if (exists) {
            setSelectedTimepoint(String(initialTimepoint));
        }
    }
}, [initialTimepoint, timepoints]);

// Set currentTimepoint from timepoints list when selection changes
useEffect(() => {
    console.log('Selected timepoint changed:', selectedTimepoint);
    console.log('Available timepoints:', timepoints);
    if (selectedTimepoint && Array.isArray(timepoints)) {
        const selected = timepoints.find(t => String(t?.id) === String(selectedTimepoint));
        console.log('Found timepoint:', selected);
        if (selected) {
            setCurrentTimepoint(selected);
        }
    }
}, [selectedTimepoint, timepoints]);

useEffect(() => {
    const fetchModels = async () => {
        try {
            console.log('Fetching models...');
            const response = await fetch(`${API_BASE_URL}/llm/models`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log('Fetched models:', data);
            
            // Validate data structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid models data format');
            }
            
            console.log('Raw models data:', data);
            const processedData = Object.entries(data).reduce((acc, [provider, models]) => {
                acc[provider] = Array.isArray(models) ? models : [];
                return acc;
            }, {});
            
            console.log('Processed models data:', processedData);
            if (Object.keys(processedData).length > 0) {
                console.log('Models data received:', processedData);
                setProviders(Object.keys(processedData));
                setModels(processedData);
                setModelsLoaded(true);
            } else {
                console.warn('No models found in response');
                setError('No available models found');
            }
        } catch (error) {
            console.error('Error fetching models:', error);
            setError('Failed to load models. Please try refreshing the page.');
        }
    };
    
    fetchModels();
    
    // Clean up function
    return () => {
        setProviders([]);
        setModels({});
    };
}, []);

// Separate useEffect to handle setting the default model
useEffect(() => {
    if (modelsLoaded && !selectedModel) {
        console.log('Setting default model...');
        const allModels = Object.values(models).flat();
        console.log('Available models:', allModels);
        
        const defaultModel = allModels.find(m => m.id === 'claude-instant-1');
        if (defaultModel) {
            console.log('Setting claude-instant-1 as default model');
            setSelectedModel(defaultModel.id);
        } else if (allModels.length > 0) {
            console.log('claude-instant-1 not available, using first available model:', allModels[0].id);
            setSelectedModel(allModels[0].id);
        } else {
            console.warn('No models available to set as default');
        }
    }
}, [modelsLoaded, models, selectedModel]);

const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
};

useEffect(() => {
    scrollToBottom();
}, [messages]);

const handlePromptChange = async (event) => {
    const promptId = event.target.value;
    setSelectedPrompt(promptId);
    
    try {
        setIsLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE_URL}/llm/prompts/${promptId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data || !data.prompt || !data.prompt.content) {
            throw new Error('Invalid prompt data received');
        }
        
        setMessages([{
            role: 'system',
            content: data.prompt.content
        }]);
    } catch (error) {
        console.error('Error loading prompt:', error);
        setError(`Failed to load prompt: ${error.message}`);
        setMessages([]); // Clear messages on error
    } finally {
        setIsLoading(false);
    }
};

const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const newMessage = {
    role: 'user',
    content: inputMessage
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
    const response = await fetch(`${API_BASE_URL}/llm/chat`, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            messages: [...messages, newMessage],
            model: selectedModel,
            timepoint_id: selectedTimepoint,
            original_graph: currentTimepoint?.original_graph,
            split_graph: currentTimepoint?.split_graph,
        }),
    });

    const data = await response.json();
    setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.response
    }]);
    } catch (error) {
    console.error('Error sending message:', error);
    } finally {
    setIsLoading(false);
    }
};

return (
    <Container maxWidth="lg">
    {error && (
        <Box sx={{ mt: 2, mb: 2 }}>
            <Typography color="error" variant="body1">
                {error}
            </Typography>
        </Box>
    )}
    <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
            LLM Analysis Interface
        </Typography>
        {currentTimepoint && (
            <Typography variant="body1" gutterBottom sx={{ color: 'text.secondary' }}>
                Current Timepoint: {currentTimepoint.id} {currentTimepoint.timestamp && `(${new Date(currentTimepoint.timestamp).toLocaleString()})`}
            </Typography>
        )}
        
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
            <FormControl fullWidth>
                <InputLabel>Select Timepoint</InputLabel>
                <Select
                    value={selectedTimepoint || ''}
                    label="Select Timepoint"
                    onChange={(e) => {
                        console.log('Timepoint selection changed to:', e.target.value);
                        setSelectedTimepoint(e.target.value);
                    }}
                >
                    {Array.isArray(timepoints) && timepoints.map((timepoint) => (
                        <MenuItem key={timepoint?.id || ''} value={String(timepoint?.id || '')}>
                            {timepoint?.name || `Timepoint ${timepoint?.id || ''}`}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
            <FormControl fullWidth>
            <InputLabel>Select Prompt</InputLabel>
            <Select
            value={selectedPrompt}
            label="Select Prompt"
            onChange={handlePromptChange}
            >
            {Array.isArray(prompts) && prompts.map((prompt) => (
                <MenuItem key={prompt?.id || 'default'} value={prompt?.id || ''}>
                    {prompt?.name || 'Unnamed Prompt'}
                </MenuItem>
            ))}
            </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Model</InputLabel>
            <Select
                value={selectedModel || ''}
                label="Model"
                onChange={(e) => {
                    console.log('Model selection changed to:', e.target.value);
                    setSelectedModel(e.target.value);
                }}
            >
            {providers.map(provider => {
                const providerModels = models[provider] || [];
                return [
                    <MenuItem key={provider} disabled divider sx={{ backgroundColor: '#f5f5f5' }}>
                        {provider.toUpperCase()}
                    </MenuItem>,
                    ...providerModels.map(model => (
                        <MenuItem key={model.id} value={model.id}>
                            {model.name || model.id}
                        </MenuItem>
                    ))
                ];
            })}
            </Select>
        </FormControl>
        </Box>

        <Paper
        sx={{
            height: '400px',
            overflow: 'auto',
            p: 2,
            mb: 2,
            backgroundColor: '#f5f5f5',
        }}
        >
        {messages.map((message, index) => (
            <Box
            key={index}
            sx={{
                mb: 2,
                textAlign: message.role === 'user' ? 'right' : 'left',
            }}
            >
            <Paper
                sx={{
                display: 'inline-block',
                p: 2,
                maxWidth: '70%',
                backgroundColor: message.role === 'user' ? '#e3f2fd' : '#fff',
                }}
            >
                <Typography variant="body1">
                {message.content}
                </Typography>
            </Paper>
            </Box>
        ))}
        <div ref={messagesEndRef} />
        </Paper>

        <Box sx={{ display: 'flex', gap: 2 }}>
        <TextField
            fullWidth
            multiline
            rows={2}
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
        />
        <Button
            variant="contained"
            onClick={handleSendMessage}
            disabled={isLoading || !inputMessage.trim()}
            sx={{ minWidth: '120px' }}
        >
            {isLoading ? (
            <CircularProgress size={24} />
            ) : (
            <>
                Send
                <SendIcon sx={{ ml: 1 }} />
            </>
            )}
        </Button>
        </Box>
    </Box>
    </Container>
);
};

export default LLMAnalysisView;

