import { task, logger, wait } from "@trigger.dev/sdk/v3";

interface AnalyticsTrackingPayload {
  eventType: string;
  userId: string;
  properties: Record<string, any>;
  scheduledDate?: string;
  timestamp: string;
}

export const analyticsTrackingTask = task({
  id: "analytics-tracking",
  retry: {
    maxAttempts: 3,
    minTimeoutInMs: 1000,
    maxTimeoutInMs: 10000,
    factor: 2,
  },
  run: async (payload: AnalyticsTrackingPayload) => {
    logger.info("Starting analytics tracking automation", { 
      eventType: payload.eventType,
      userId: payload.userId 
    });

    // Wait until scheduled date if provided
    if (payload.scheduledDate) {
      const scheduledDateTime = new Date(payload.scheduledDate);
      logger.info("Waiting until scheduled date", { scheduledDateTime });
      
      await wait.until({ date: scheduledDateTime });
    }

    // Step 1: Process event data
    logger.info("Processing event data", { eventType: payload.eventType });
    
    const processedEvent = {
      ...payload.properties,
      event_type: payload.eventType,
      user_id: payload.userId,
      timestamp: payload.timestamp,
      processed_at: new Date().toISOString(),
      session_id: `session_${Date.now()}`,
      source: "agentos_automation"
    };

    // Step 2: Send to analytics platforms
    logger.info("Sending to analytics platforms");
    
    const analyticsResults: Array<{
      platform: string;
      status: string;
      event_id?: string;
      error?: string;
    }> = [];
    
    // Google Analytics 4 (example)
    try {
      // In real implementation, use GA4 Measurement Protocol
      logger.info("Sending to Google Analytics 4");
      analyticsResults.push({
        platform: "google_analytics",
        status: "success",
        event_id: `ga4_${Date.now()}`
      });
    } catch (error) {
      logger.error("Failed to send to Google Analytics", { error });
      analyticsResults.push({
        platform: "google_analytics",
        status: "failed",
        error: error.message
      });
    }

    // Mixpanel (example)
    try {
      logger.info("Sending to Mixpanel");
      analyticsResults.push({
        platform: "mixpanel",
        status: "success",
        event_id: `mp_${Date.now()}`
      });
    } catch (error) {
      logger.error("Failed to send to Mixpanel", { error });
      analyticsResults.push({
        platform: "mixpanel",
        status: "failed",
        error: error.message
      });
    }

    // Step 3: Store in data warehouse
    logger.info("Storing in data warehouse");
    
    const warehouseResult = {
      stored_at: new Date().toISOString(),
      record_id: `warehouse_${Date.now()}`,
      table: "user_events",
      status: "success"
    };

    // Step 4: Trigger alerts if needed
    const alertsTriggered: Array<{
      type: string;
      message: string;
      triggered_at: string;
    }> = [];
    
    if (payload.eventType === "product_launch" || payload.eventType === "signup_spike") {
      logger.info("Triggering alerts for critical event");
      
      alertsTriggered.push({
        type: "slack_notification",
        message: `Critical event detected: ${payload.eventType}`,
        triggered_at: new Date().toISOString()
      });
    }

    // Step 5: Update real-time dashboards
    logger.info("Updating real-time dashboards");
    
    const dashboardUpdates = [
      {
        dashboard: "product_metrics",
        updated_at: new Date().toISOString(),
        status: "success"
      },
      {
        dashboard: "user_activity",
        updated_at: new Date().toISOString(),
        status: "success"
      }
    ];

    const result = {
      success: true,
      event_processed: processedEvent,
      analytics_results: analyticsResults,
      warehouse_result: warehouseResult,
      alerts_triggered: alertsTriggered,
      dashboard_updates: dashboardUpdates,
      completed_at: new Date().toISOString(),
      processing_time_ms: Date.now() - new Date(payload.timestamp).getTime()
    };

    logger.info("Analytics tracking automation completed", {
      eventType: payload.eventType,
      platformsProcessed: analyticsResults.length,
      alertsTriggered: alertsTriggered.length
    });

    return result;
  },
}); 