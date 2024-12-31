import React, { useState, useEffect, useRef } from 'react';
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

const LLMAnalysisView = () => {
const [selectedPrompt, setSelectedPrompt] = useState('');
const [prompts, setPrompts] = useState([]);
const [messages, setMessages] = useState([]);
const [inputMessage, setInputMessage] = useState('');
const [isLoading, setIsLoading] = useState(false);
const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');
const messagesEndRef = useRef(null);

useEffect(() => {
    // Fetch available prompts from backend
    const fetchPrompts = async () => {
    try {
        const response = await fetch('/api/llm/prompts');
        const data = await response.json();
        setPrompts(data);
    } catch (error) {
        console.error('Error fetching prompts:', error);
    }
    };
    fetchPrompts();
}, []);

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
    const response = await fetch(`/api/llm/load-prompt/${promptId}`);
    const data = await response.json();
    
    // Add system message with loaded prompt
    setMessages([{
        role: 'system',
        content: data.content
    }]);
    } catch (error) {
    console.error('Error loading prompt:', error);
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
    const response = await fetch('/api/llm/chat', {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify({
        messages: [...messages, newMessage],
        model: selectedModel,
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
    <Box sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom>
        LLM Analysis Interface
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <FormControl fullWidth>
            <InputLabel>Select Prompt</InputLabel>
            <Select
            value={selectedPrompt}
            label="Select Prompt"
            onChange={handlePromptChange}
            >
            {prompts.map((prompt) => (
                <MenuItem key={prompt.id} value={prompt.id}>
                {prompt.name}
                </MenuItem>
            ))}
            </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Model</InputLabel>
            <Select
            value={selectedModel}
            label="Model"
            onChange={(e) => setSelectedModel(e.target.value)}
            >
            <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
            <MenuItem value="gpt-4">GPT-4</MenuItem>
            <MenuItem value="llama2">Llama 2</MenuItem>
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

