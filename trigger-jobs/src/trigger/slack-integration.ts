import { task } from "@trigger.dev/sdk/v3";
import { WebClient } from "@slack/web-api";

// Slack integration task for Agent OS
export const sendSlackMessage = task({
  id: "agent-os-slack-message",
  run: async (payload: {
    channel: string;
    message: string;
    agent_name?: string;
    user_id?: string;
  }) => {
    // Initialize Slack client with bot token
    const slack = new WebClient(process.env.SLACK_BOT_TOKEN);
    
    // Format message with Agent OS branding
    const formattedMessage = payload.agent_name 
      ? `🤖 *${payload.agent_name}* from Agent OS:\n\n${payload.message}`
      : `🤖 *Agent OS*:\n\n${payload.message}`;
    
    try {
      // Send message to Slack
      const result = await slack.chat.postMessage({
        channel: payload.channel,
        text: formattedMessage,
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: formattedMessage
            }
          },
          {
            type: "context",
            elements: [
              {
                type: "mrkdwn",
                text: `Sent by Agent OS • ${new Date().toLocaleString()}`
              }
            ]
          }
        ]
      });
      
      return {
        success: true,
        message_ts: result.ts,
        channel: result.channel,
        agent_name: payload.agent_name,
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.error("Slack message failed:", error);
      throw error;
    }
  },
});

// Task to create Slack channels for Agent OS
export const createSlackChannel = task({
  id: "agent-os-create-channel",
  run: async (payload: {
    channel_name: string;
    purpose?: string;
    is_private?: boolean;
  }) => {
    const slack = new WebClient(process.env.SLACK_BOT_TOKEN);
    
    try {
      // Create the channel
      const result = await slack.conversations.create({
        name: payload.channel_name,
        is_private: payload.is_private || false,
        purpose: payload.purpose || `Channel created by Agent OS`
      });
      
      // Send welcome message
      if (result.channel?.id) {
        await slack.chat.postMessage({
          channel: result.channel.id,
          text: `🎉 Welcome to #${payload.channel_name}!\n\nThis channel was created by Agent OS to help organize your team's workflow.`,
          blocks: [
            {
              type: "section",
              text: {
                type: "mrkdwn",
                text: `🎉 *Welcome to #${payload.channel_name}!*\n\nThis channel was created by Agent OS to help organize your team's workflow.`
              }
            },
            {
              type: "divider"
            },
            {
              type: "section",
              text: {
                type: "mrkdwn",
                text: "Agent OS can help you:\n• Send automated notifications\n• Share project updates\n• Coordinate team activities\n• Track important milestones"
              }
            }
          ]
        });
      }
      
      return {
        success: true,
        channel_id: result.channel?.id,
        channel_name: payload.channel_name,
        created_at: new Date().toISOString()
      };
      
    } catch (error) {
      console.error("Channel creation failed:", error);
      throw error;
    }
  },
});

// Task to get Slack workspace info for Agent OS setup
export const getSlackWorkspaceInfo = task({
  id: "agent-os-slack-workspace-info",
  run: async () => {
    const slack = new WebClient(process.env.SLACK_BOT_TOKEN);
    
    try {
      // Get workspace info
      const teamInfo = await slack.team.info();
      
      // Get channels list
      const channels = await slack.conversations.list({
        types: "public_channel,private_channel",
        limit: 100
      });
      
      // Get bot info
      const authTest = await slack.auth.test();
      
      return {
        success: true,
        workspace: {
          name: teamInfo.team?.name,
          id: teamInfo.team?.id,
          domain: teamInfo.team?.domain
        },
        bot: {
          user_id: authTest.user_id,
          bot_id: authTest.bot_id,
          user: authTest.user
        },
        channels: channels.channels?.map(channel => ({
          id: channel.id,
          name: channel.name,
          is_private: channel.is_private,
          is_member: channel.is_member
        })) || [],
        integration_status: "connected",
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.error("Workspace info failed:", error);
      throw error;
    }
  },
});

// Demo task to show Agent OS Slack integration working
export const demoAgentOSSlackIntegration = task({
  id: "demo-agent-os-slack-integration",
  run: async (payload: {
    demo_channel?: string;
    user_name?: string;
  }) => {
    const slack = new WebClient(process.env.SLACK_BOT_TOKEN);
    const channel = payload.demo_channel || "general";
    const userName = payload.user_name || "Demo User";
    
    try {
      // Send demo message showing Agent OS capabilities
      const result = await slack.chat.postMessage({
        channel: channel,
        text: `🚀 Agent OS is now connected to your Slack workspace!`,
        blocks: [
          {
            type: "header",
            text: {
              type: "plain_text",
              text: "🚀 Agent OS Connected!"
            }
          },
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `Hey ${userName}! Agent OS is now successfully integrated with your Slack workspace.`
            }
          },
          {
            type: "divider"
          },
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: "*What can Agent OS do in Slack?*\n\n🤖 *Alex* - Strategic planning updates\n🎨 *Dana* - Creative content sharing\n📊 *Riley* - Data insights and reports\n⚙️ *Jamie* - Operations notifications"
            }
          },
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: "*Ready to get started?*\nYour agents can now send updates, share files, and keep your team in sync automatically!"
            }
          },
          {
            type: "context",
            elements: [
              {
                type: "mrkdwn",
                text: `Connected via Agent OS • ${new Date().toLocaleString()}`
              }
            ]
          }
        ]
      });
      
      return {
        success: true,
        demo_completed: true,
        message_sent: true,
        channel: channel,
        message_ts: result.ts,
        next_steps: [
          "Your Slack workspace is connected to Agent OS",
          "All 4 agents (Alex, Dana, Riley, Jamie) can now send messages",
          "You can test the integration from the Agent OS chat interface",
          "Set up automated workflows in the Agent OS dashboard"
        ],
        timestamp: new Date().toISOString()
      };
      
    } catch (error) {
      console.error("Demo integration failed:", error);
      throw error;
    }
  },
}); 