/**
 * API Bridge for triggering Trigger.dev tasks from external services
 * This follows the v3 pattern of importing and triggering tasks directly
 */

import express from 'express';
import cors from 'cors';
import { productHuntLaunchTask } from './trigger/product-hunt-launch';
import { contentGenerationTask } from './trigger/content-generation';
import { analyticsTrackingTask } from './trigger/analytics-tracking';

const app = express();
const port = process.env.TRIGGER_API_PORT || 3001;

app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    tasks: ['product-hunt-launch', 'content-generation', 'analytics-tracking']
  });
});

// Trigger Product Hunt Launch
app.post('/trigger/product-hunt-launch', async (req, res) => {
  try {
    const payload = req.body;
    
    // Validate required fields
    if (!payload.productName || !payload.launchDate || !payload.description || !payload.website) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: productName, launchDate, description, website'
      });
    }

    // Trigger the task using the v3 pattern
    const handle = await productHuntLaunchTask.trigger(payload);
    
    res.json({
      success: true,
      task_id: 'product-hunt-launch',
      run_id: handle.id,
      status: 'triggered',
      triggered_at: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error triggering Product Hunt launch:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      task_id: 'product-hunt-launch'
    });
  }
});

// Trigger Content Generation
app.post('/trigger/content-generation', async (req, res) => {
  try {
    const payload = req.body;
    
    // Validate required fields
    if (!payload.contentType || !payload.topic || !payload.targetAudience) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: contentType, topic, targetAudience'
      });
    }

    // Trigger the task using the v3 pattern
    const handle = await contentGenerationTask.trigger(payload);
    
    res.json({
      success: true,
      task_id: 'content-generation',
      run_id: handle.id,
      status: 'triggered',
      triggered_at: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error triggering content generation:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      task_id: 'content-generation'
    });
  }
});

// Trigger Analytics Tracking
app.post('/trigger/analytics-tracking', async (req, res) => {
  try {
    const payload = req.body;
    
    // Validate required fields
    if (!payload.eventType || !payload.userId || !payload.properties) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: eventType, userId, properties'
      });
    }

    // Trigger the task using the v3 pattern
    const handle = await analyticsTrackingTask.trigger(payload);
    
    res.json({
      success: true,
      task_id: 'analytics-tracking',
      run_id: handle.id,
      status: 'triggered',
      triggered_at: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('Error triggering analytics tracking:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      task_id: 'analytics-tracking'
    });
  }
});

// Get run status (this would need to be implemented with Trigger.dev SDK)
app.get('/runs/:runId', async (req, res) => {
  try {
    const { runId } = req.params;
    
    // In a real implementation, you'd use the Trigger.dev SDK to get run status
    // For now, return a mock response
    res.json({
      id: runId,
      status: 'running',
      createdAt: new Date().toISOString(),
      // This would be real data from Trigger.dev
    });
    
  } catch (error) {
    console.error('Error getting run status:', error);
    res.status(500).json({
      error: error.message
    });
  }
});

app.listen(port, () => {
  console.log(`🚀 Trigger.dev API Bridge running on port ${port}`);
  console.log(`Health check: http://localhost:${port}/health`);
}); 