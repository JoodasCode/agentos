import {
  logger,
  task,
  wait
} from "../../../../../../chunk-DY4YI7G3.mjs";
import {
  init_esm
} from "../../../../../../chunk-XVMCOVNG.mjs";

// src/trigger/content-generation.ts
init_esm();
var contentGenerationTask = task({
  id: "content-generation",
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 2e3,
    maxTimeoutInMs: 15e3,
    factor: 2
  },
  run: async (payload) => {
    logger.info("Starting content generation automation", {
      contentType: payload.contentType,
      topic: payload.topic,
      targetAudience: payload.targetAudience
    });
    const generatedContent = await generateContent(payload);
    if (payload.scheduledDate) {
      const scheduledDateTime = new Date(payload.scheduledDate);
      logger.info("Waiting until scheduled publication date", { scheduledDateTime });
      await wait.until({ date: scheduledDateTime });
    }
    const publishResults = await publishContent(payload, generatedContent);
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
      completedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
  }
});
async function generateContent(payload) {
  logger.info("Generating content", { contentType: payload.contentType });
  await wait.for({ seconds: 5 });
  const contentTemplates = {
    "blog-post": {
      title: `The Ultimate Guide to ${payload.topic}`,
      content: `# The Ultimate Guide to ${payload.topic}

This comprehensive guide covers everything you need to know about ${payload.topic} for ${payload.targetAudience}.

## Introduction

In today's fast-paced world, understanding ${payload.topic} is crucial for ${payload.targetAudience}.

## Key Points

1. Understanding the basics
2. Advanced techniques
3. Best practices
4. Common pitfalls to avoid

## Conclusion

By following these guidelines, you'll be well-equipped to master ${payload.topic}.`,
      wordCount: 250,
      readingTime: "2 min"
    },
    "social-media": {
      posts: [
        `🚀 Excited to share insights about ${payload.topic}! Perfect for ${payload.targetAudience} looking to level up. #${payload.topic.replace(/\s+/g, "")}`,
        `💡 Pro tip: When working with ${payload.topic}, remember that consistency is key. What's your experience? Share below! 👇`,
        `🎯 Quick question for ${payload.targetAudience}: What's your biggest challenge with ${payload.topic}? Let's discuss! 💬`
      ],
      hashtags: [`#${payload.topic.replace(/\s+/g, "")}`, "#productivity", "#tips"],
      platforms: payload.platforms || ["twitter", "linkedin"]
    },
    "email-campaign": {
      subject: `Master ${payload.topic}: Essential Tips for ${payload.targetAudience}`,
      preheader: `Everything you need to know about ${payload.topic}`,
      content: `Hi there!

We've put together some essential insights about ${payload.topic} specifically for ${payload.targetAudience}.

Key takeaways:
• Understanding the fundamentals
• Practical implementation strategies
• Common mistakes to avoid

Ready to dive deeper? Let's get started!

Best regards,
The Team`,
      cta: "Learn More"
    },
    "product-description": {
      title: `${payload.topic} Solution`,
      shortDescription: `The perfect ${payload.topic} solution for ${payload.targetAudience}`,
      longDescription: `Our comprehensive ${payload.topic} solution is designed specifically for ${payload.targetAudience}. With advanced features and intuitive design, it's the perfect tool to streamline your workflow and boost productivity.`,
      features: [
        "Easy to use interface",
        "Advanced automation",
        "Real-time analytics",
        "24/7 support"
      ],
      benefits: [
        "Save time and effort",
        "Increase productivity",
        "Better results",
        "Peace of mind"
      ]
    }
  };
  const content = contentTemplates[payload.contentType];
  logger.info("Content generated successfully", {
    contentType: payload.contentType,
    contentPreview: typeof content === "object" ? JSON.stringify(content).substring(0, 100) + "..." : content
  });
  return content;
}
async function publishContent(payload, content) {
  logger.info("Publishing content to integrations");
  const results = {};
  if (payload.integrations.notion) {
    try {
      logger.info("Publishing to Notion");
      await wait.for({ seconds: 2 });
      results.notion = {
        success: true,
        pageId: "notion-page-" + Date.now(),
        url: `https://notion.so/page-${Date.now()}`
      };
      logger.info("Successfully published to Notion", results.notion);
    } catch (error) {
      logger.error("Failed to publish to Notion", { error });
      results.notion = { success: false, error: error.message };
    }
  }
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
              text: `*📝 New ${payload.contentType} generated!*

*Topic:* ${payload.topic}
*Target Audience:* ${payload.targetAudience}
*Tone:* ${payload.tone}`
            }
          }
        ]
      };
      const response = await fetch(payload.integrations.slack.webhook, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
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
async function sendCompletionNotifications(payload, content, publishResults) {
  logger.info("Sending completion notifications");
  const summary = {
    contentType: payload.contentType,
    topic: payload.topic,
    targetAudience: payload.targetAudience,
    tone: payload.tone,
    publishedTo: Object.keys(publishResults).filter((key) => publishResults[key].success),
    failedPublications: Object.keys(publishResults).filter((key) => !publishResults[key].success)
  };
  logger.info("Content generation summary", summary);
  return summary;
}
export {
  contentGenerationTask
};
//# sourceMappingURL=content-generation.mjs.map
