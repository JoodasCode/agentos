import {
  logger,
  task,
  wait
} from "../../../../../../chunk-DY4YI7G3.mjs";
import {
  init_esm
} from "../../../../../../chunk-XVMCOVNG.mjs";

// src/trigger/product-hunt-launch.ts
init_esm();
var productHuntLaunchTask = task({
  id: "product-hunt-launch",
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 1e3,
    maxTimeoutInMs: 1e4,
    factor: 2
  },
  run: async (payload) => {
    logger.info("Starting Product Hunt launch automation", {
      product: payload.productName,
      launchDate: payload.launchDate
    });
    const launchDateTime = new Date(payload.launchDate);
    logger.info("Waiting until launch date", { launchDateTime });
    await wait.until({ date: launchDateTime });
    logger.info("Launch date reached! Starting automation sequence");
    if (payload.slackWebhook) {
      await sendSlackNotification(payload);
    }
    if (payload.twitterHandle) {
      await scheduleTwitterPosts(payload);
    }
    await monitorLaunchDay(payload);
    logger.info("Product Hunt launch automation completed", {
      product: payload.productName
    });
    return {
      success: true,
      product: payload.productName,
      launchDate: payload.launchDate,
      completedAt: (/* @__PURE__ */ new Date()).toISOString()
    };
  }
});
async function sendSlackNotification(payload) {
  logger.info("Sending Slack notification");
  try {
    const response = await fetch(payload.slackWebhook, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        text: `🚀 ${payload.productName} is now live on Product Hunt!`,
        blocks: [
          {
            type: "section",
            text: {
              type: "mrkdwn",
              text: `*🚀 ${payload.productName} is now live on Product Hunt!*

${payload.description}

<${payload.website}|Visit Website>`
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
async function scheduleTwitterPosts(payload) {
  logger.info("Scheduling Twitter posts");
  const tweets = [
    `🚀 We're live on Product Hunt! ${payload.productName} - ${payload.description} Check it out: ${payload.website} #ProductHunt #Launch`,
    `🎉 Thank you to everyone supporting ${payload.productName} on Product Hunt today! Your votes mean the world to us 🙏`,
    `⏰ Last chance to support ${payload.productName} on Product Hunt! Every vote counts 🗳️ ${payload.website}`
  ];
  const tweetTimes = [0, 4, 8];
  for (let i = 0; i < tweets.length; i++) {
    const tweetTime = new Date(Date.now() + tweetTimes[i] * 60 * 60 * 1e3);
    logger.info(`Scheduling tweet ${i + 1} for ${tweetTime.toISOString()}`);
    await wait.until({ date: tweetTime });
    logger.info(`Tweet ${i + 1} would be posted now`, { content: tweets[i] });
  }
}
async function monitorLaunchDay(payload) {
  logger.info("Starting launch day monitoring");
  const monitoringHours = 12;
  const updateInterval = 2;
  for (let hour = 0; hour < monitoringHours; hour += updateInterval) {
    await wait.for({ hours: updateInterval });
    logger.info(`Launch day update - ${hour + updateInterval} hours elapsed`, {
      product: payload.productName,
      hoursElapsed: hour + updateInterval
    });
  }
  logger.info("Launch day monitoring completed");
}
export {
  productHuntLaunchTask
};
//# sourceMappingURL=product-hunt-launch.mjs.map
