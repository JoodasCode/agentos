/**
 * API Bridge for triggering Trigger.dev tasks from external services
 * This follows the v3 pattern of importing and triggering tasks directly
 */

import express from 'express';
import cors from 'cors';
import { productHuntLaunchTask } from './trigger/product-hunt-launch';
import { contentGenerationTask } from './trigger/content-generation';
import { analyticsTrackingTask } from './trigger/analytics-tracking';
import { sendSlackMessage, createSlackChannel, getSlackWorkspaceInfo, demoAgentOSSlackIntegration } from './trigger/slack-integration';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'Trigger.dev API Server',
    timestamp: new Date().toISOString()
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

// Slack Integration Endpoints
app.post('/api/trigger/send-slack-message', async (req, res) => {
  try {
    const { slack_bot_token, channel, message, user_name } = req.body;
    
    // Set environment variable for this request
    process.env.SLACK_BOT_TOKEN = slack_bot_token;
    
    // Trigger the Slack message task with correct parameters
    const handle = await sendSlackMessage.trigger({
      channel: channel || 'general',
      message: message || `Hello from Agent OS! Message sent by ${user_name || 'Agent'}`,
      agent_name: user_name || 'Agent'
    });

    res.json({
      success: true,
      taskId: handle.id,
      message: 'Slack message task triggered successfully',
      handle: handle
    });
  } catch (error) {
    console.error('Error triggering Slack message task:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/trigger/slack-workspace-info', async (req, res) => {
  try {
    const { slack_bot_token } = req.body;
    
    // Set environment variable for this request
    process.env.SLACK_BOT_TOKEN = slack_bot_token;
    
    // Trigger the workspace info task (no parameters needed)
    const handle = await getSlackWorkspaceInfo.trigger();

    res.json({
      success: true,
      taskId: handle.id,
      message: 'Slack workspace info task triggered successfully',
      handle: handle
    });
  } catch (error) {
    console.error('Error triggering Slack workspace info task:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/trigger/demo-slack-integration', async (req, res) => {
  try {
    const { slack_bot_token, demo_channel, user_name } = req.body;
    
    // Set environment variable for this request
    process.env.SLACK_BOT_TOKEN = slack_bot_token;
    
    // Trigger the demo integration task with correct parameters
    const handle = await demoAgentOSSlackIntegration.trigger({
      demo_channel: demo_channel || 'general',
      user_name: user_name || 'Demo User'
    });

    res.json({
      success: true,
      taskId: handle.id,
      message: 'Slack demo integration task triggered successfully',
      handle: handle,
      next_steps: [
        "✅ Demo message sent to Slack",
        "🤖 Agent OS is now connected to your workspace",
        "💬 Your agents can send messages to any channel",
        "🚀 Try asking Dana to send a message!"
      ]
    });
  } catch (error) {
    console.error('Error triggering Slack demo task:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.post('/api/trigger/create-slack-channel', async (req, res) => {
  try {
    const { slack_bot_token, channel_name, is_private, purpose } = req.body;
    
    // Set environment variable for this request
    process.env.SLACK_BOT_TOKEN = slack_bot_token;
    
    // Trigger the create channel task with correct parameters
    const handle = await createSlackChannel.trigger({
      channel_name: channel_name,
      is_private: is_private || false,
      purpose: purpose
    });

    res.json({
      success: true,
      taskId: handle.id,
      message: 'Slack channel creation task triggered successfully',
      handle: handle
    });
  } catch (error) {
    console.error('Error triggering Slack channel creation task:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Agent-specific endpoints for direct task triggering
app.post('/api/agents/dana/send-slack-message', async (req, res) => {
  try {
    const { slack_bot_token, channel, message } = req.body;
    
    // Set environment variable for this request
    process.env.SLACK_BOT_TOKEN = slack_bot_token;
    
    // Dana-specific Slack message with branding
    const danaMessage = `🎨 **Dana (Creative Agent)**: ${message}`;
    
    const handle = await sendSlackMessage.trigger({
      channel: channel || 'general',
      message: danaMessage,
      agent_name: 'Dana (Agent OS)'
    });

    res.json({
      success: true,
      agent: 'Dana',
      taskId: handle.id,
      message: 'Dana sent your Slack message!',
      handle: handle
    });
  } catch (error) {
    console.error('Error with Dana Slack message:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Trigger.dev API Server running on port ${PORT}`);
  console.log(`📡 Health check: http://localhost:${PORT}/health`);
  console.log(`💬 Slack endpoints available at /api/trigger/*`);
}); 