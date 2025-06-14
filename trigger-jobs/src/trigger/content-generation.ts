import { task, logger, wait } from "@trigger.dev/sdk/v3";

interface ContentGenerationPayload {
  contentType: 'blog-post' | 'social-media' | 'email-campaign' | 'product-description';
  topic: string;
  targetAudience: string;
  tone: 'professional' | 'casual' | 'friendly' | 'technical';
  platforms?: string[];
  scheduledDate?: string;
  integrations: {
    notion?: {
      databaseId: string;
      apiKey: string;
    };
    slack?: {
      webhook: string;
      channel: string;
    };
  };
}

export const contentGenerationTask = task({
  id: "content-generation",
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 2000,
    maxTimeoutInMs: 15000,
    factor: 2,
  },
  run: async (payload: ContentGenerationPayload) => {
    logger.info("Starting content generation automation", { 
      contentType: payload.contentType,
      topic: payload.topic,
      targetAudience: payload.targetAudience
    });

    // Step 1: Generate content based on type
    const generatedContent = await generateContent(payload);
    
    // Step 2: If scheduled, wait until the scheduled time
    if (payload.scheduledDate) {
      const scheduledDateTime = new Date(payload.scheduledDate);
      logger.info("Waiting until scheduled publication date", { scheduledDateTime });
      await wait.until({ date: scheduledDateTime });
    }

    // Step 3: Publish to integrations
    const publishResults = await publishContent(payload, generatedContent);

    // Step 4: Send notifications
    await sendCompletionNotifications(payload, generatedContent, publishResults);

    logger.info("Content generation automation completed", {
      contentType: payload.contentType,
      topic: payload.topic
    });

    return {
      success: true,
      contentType: payload.contentType,
      topic: payload.topic,
      generatedContent,
      publishResults,
      completedAt: new Date().toISOString()
    };
  },
});

async function generateContent(payload: ContentGenerationPayload) {
  logger.info("Generating content", { contentType: payload.contentType });

  // In a real implementation, this would call OpenAI or another LLM
  // For now, we'll simulate content generation
  await wait.for({ seconds: 5 }); // Simulate processing time

  const contentTemplates = {
    'blog-post': {
      title: `The Ultimate Guide to ${payload.topic}`,
      content: `# The Ultimate Guide to ${payload.topic}\n\nThis comprehensive guide covers everything you need to know about ${payload.topic} for ${payload.targetAudience}.\n\n## Introduction\n\nIn today's fast-paced world, understanding ${payload.topic} is crucial for ${payload.targetAudience}.\n\n## Key Points\n\n1. Understanding the basics\n2. Advanced techniques\n3. Best practices\n4. Common pitfalls to avoid\n\n## Conclusion\n\nBy following these guidelines, you'll be well-equipped to master ${payload.topic}.`,
      wordCount: 250,
      readingTime: '2 min'
    },
    'social-media': {
      posts: [
        `🚀 Excited to share insights about ${payload.topic}! Perfect for ${payload.targetAudience} looking to level up. #${payload.topic.replace(/\s+/g, '')}`,
        `💡 Pro tip: When working with ${payload.topic}, remember that consistency is key. What's your experience? Share below! 👇`,
        `🎯 Quick question for ${payload.targetAudience}: What's your biggest challenge with ${payload.topic}? Let's discuss! 💬`
      ],
      hashtags: [`#${payload.topic.replace(/\s+/g, '')}`, '#productivity', '#tips'],
      platforms: payload.platforms || ['twitter', 'linkedin']
    },
    'email-campaign': {
      subject: `Master ${payload.topic}: Essential Tips for ${payload.targetAudience}`,
      preheader: `Everything you need to know about ${payload.topic}`,
      content: `Hi there!\n\nWe've put together some essential insights about ${payload.topic} specifically for ${payload.targetAudience}.\n\nKey takeaways:\n• Understanding the fundamentals\n• Practical implementation strategies\n• Common mistakes to avoid\n\nReady to dive deeper? Let's get started!\n\nBest regards,\nThe Team`,
      cta: 'Learn More'
    },
    'product-description': {
      title: `${payload.topic} Solution`,
      shortDescription: `The perfect ${payload.topic} solution for ${payload.targetAudience}`,
      longDescription: `Our comprehensive ${payload.topic} solution is designed specifically for ${payload.targetAudience}. With advanced features and intuitive design, it's the perfect tool to streamline your workflow and boost productivity.`,
      features: [
        'Easy to use interface',
        'Advanced automation',
        'Real-time analytics',
        '24/7 support'
      ],
      benefits: [
        'Save time and effort',
        'Increase productivity',
        'Better results',
        'Peace of mind'
      ]
    }
  };

  const content = contentTemplates[payload.contentType];
  
  logger.info("Content generated successfully", { 
    contentType: payload.contentType,
    contentPreview: typeof content === 'object' ? JSON.stringify(content).substring(0, 100) + '...' : content
  });

  return content;
}

async function publishContent(payload: ContentGenerationPayload, content: any) {
  logger.info("Publishing content to integrations");
  const results: any = {};

  // Publish to Notion if configured
  if (payload.integrations.notion) {
    try {
      logger.info("Publishing to Notion");
      
      // In a real implementation, this would use the Notion API
      await wait.for({ seconds: 2 }); // Simulate API call
      
      results.notion = {
        success: true,
        pageId: 'notion-page-' + Date.now(),
        url: `https://notion.so/page-${Date.now()}`
      };
      
      logger.info("Successfully published to Notion", results.notion);
    } catch (error) {
      logger.error("Failed to publish to Notion", { error });
      results.notion = { success: false, error: error.message };
    }
  }

  // Send to Slack if configured
  if (payload.integrations.slack) {
    try {
      logger.info("Sending content summary to Slack");
      
      const slackMessage = {
        text: `📝 New ${payload.contentType} generated!`,
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `*📝 New ${payload.contentType} generated!*\n\n*Topic:* ${payload.topic}\n*Target Audience:* ${payload.targetAudience}\n*Tone:* ${payload.tone}`
            }
          }
        ]
      };

      const response = await fetch(payload.integrations.slack.webhook, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(slackMessage)
      });

      if (!response.ok) {
        throw new Error(`Slack API error: ${response.statusText}`);
      }

      results.slack = { success: true, channel: payload.integrations.slack.channel };
      logger.info("Successfully sent to Slack", results.slack);
    } catch (error) {
      logger.error("Failed to send to Slack", { error });
      results.slack = { success: false, error: error.message };
    }
  }

  return results;
}

async function sendCompletionNotifications(payload: ContentGenerationPayload, content: any, publishResults: any) {
  logger.info("Sending completion notifications");

  // Summary of what was accomplished
  const summary = {
    contentType: payload.contentType,
    topic: payload.topic,
    targetAudience: payload.targetAudience,
    tone: payload.tone,
    publishedTo: Object.keys(publishResults).filter(key => publishResults[key].success),
    failedPublications: Object.keys(publishResults).filter(key => !publishResults[key].success)
  };

  logger.info("Content generation summary", summary);

  // In a real implementation, this could:
  // - Send email notifications
  // - Update project management tools
  // - Trigger follow-up workflows
  // - Log analytics events

  return summary;
} 