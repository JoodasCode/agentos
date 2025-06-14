import { task, logger, wait } from "@trigger.dev/sdk/v3";

interface ProductHuntLaunchPayload {
  productName: string;
  launchDate: string;
  description: string;
  website: string;
  twitterHandle?: string;
  slackWebhook?: string;
}

export const productHuntLaunchTask = task({
  id: "product-hunt-launch",
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 10000,
    factor: 2,
  },
  run: async (payload: ProductHuntLaunchPayload) => {
    logger.info("Starting Product Hunt launch automation", { 
      product: payload.productName,
      launchDate: payload.launchDate 
    });

    // Wait until launch date
    const launchDateTime = new Date(payload.launchDate);
    logger.info("Waiting until launch date", { launchDateTime });
    
    await wait.until({ date: launchDateTime });
    
    logger.info("Launch date reached! Starting automation sequence");

    // Step 1: Send launch notification
    if (payload.slackWebhook) {
      await sendSlackNotification(payload);
    }

    // Step 2: Post to social media
    if (payload.twitterHandle) {
      await scheduleTwitterPosts(payload);
    }

    // Step 3: Monitor and send updates throughout the day
    await monitorLaunchDay(payload);

    logger.info("Product Hunt launch automation completed", {
      product: payload.productName
    });

    return {
      success: true,
      product: payload.productName,
      launchDate: payload.launchDate,
      completedAt: new Date().toISOString()
    };
  },
});

async function sendSlackNotification(payload: ProductHuntLaunchPayload) {
  logger.info("Sending Slack notification");
  
  try {
    const response = await fetch(payload.slackWebhook!, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: `🚀 ${payload.productName} is now live on Product Hunt!`,
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `*🚀 ${payload.productName} is now live on Product Hunt!*\n\n${payload.description}\n\n<${payload.website}|Visit Website>`
            }
          }
        ]
      })
    });

    if (!response.ok) {
      throw new Error(`Slack notification failed: ${response.statusText}`);
    }

    logger.info("Slack notification sent successfully");
  } catch (error) {
    logger.error("Failed to send Slack notification", { error });
    throw error;
  }
}

async function scheduleTwitterPosts(payload: ProductHuntLaunchPayload) {
  logger.info("Scheduling Twitter posts");
  
  const tweets = [
    `🚀 We're live on Product Hunt! ${payload.productName} - ${payload.description} Check it out: ${payload.website} #ProductHunt #Launch`,
    `🎉 Thank you to everyone supporting ${payload.productName} on Product Hunt today! Your votes mean the world to us 🙏`,
    `⏰ Last chance to support ${payload.productName} on Product Hunt! Every vote counts 🗳️ ${payload.website}`
  ];

  // Schedule tweets throughout the day
  const tweetTimes = [0, 4, 8]; // Hours after launch
  
  for (let i = 0; i < tweets.length; i++) {
    const tweetTime = new Date(Date.now() + (tweetTimes[i] * 60 * 60 * 1000));
    logger.info(`Scheduling tweet ${i + 1} for ${tweetTime.toISOString()}`);
    
    // In a real implementation, this would integrate with Twitter API
    // For now, we'll just log the scheduled tweets
    await wait.until({ date: tweetTime });
    logger.info(`Tweet ${i + 1} would be posted now`, { content: tweets[i] });
  }
}

async function monitorLaunchDay(payload: ProductHuntLaunchPayload) {
  logger.info("Starting launch day monitoring");
  
  // Monitor for 12 hours with updates every 2 hours
  const monitoringHours = 12;
  const updateInterval = 2;
  
  for (let hour = 0; hour < monitoringHours; hour += updateInterval) {
    await wait.for({ hours: updateInterval });
    
    logger.info(`Launch day update - ${hour + updateInterval} hours elapsed`, {
      product: payload.productName,
      hoursElapsed: hour + updateInterval
    });
    
    // In a real implementation, this would:
    // - Check Product Hunt ranking
    // - Send progress updates to Slack
    // - Trigger additional marketing actions based on performance
  }
  
  logger.info("Launch day monitoring completed");
} 