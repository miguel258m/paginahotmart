// OneSignal Configuration
// Replace 'YOUR_APP_ID' with your actual OneSignal App ID

window.OneSignalDeferred = window.OneSignalDeferred || [];

OneSignalDeferred.push(async function(OneSignal) {
  await OneSignal.init({
    appId: "YOUR_APP_ID", // Replace with your OneSignal App ID
    safari_web_id: "web.onesignal.auto.xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    notifyButton: {
      enable: false,
    },
    allowLocalhostAsSecureOrigin: true,
  });

  // Check if user is subscribed
  const isPushSupported = await OneSignal.Notifications.isPushSupported();
  console.log('Push supported:', isPushSupported);

  // Listen for subscription changes
  OneSignal.User.PushSubscription.addEventListener('change', function(event) {
    console.log('Push subscription changed:', event);
    if (event.current.optedIn) {
      console.log('User is subscribed to push notifications');
      updateNotificationIndicator();
    }
  });
});

// Function to request permission
async function requestOneSignalPermission() {
  try {
    await OneSignal.Notifications.requestPermission();
    const permission = await OneSignal.Notifications.permission;
    console.log('OneSignal permission:', permission);
    
    if (permission) {
      alert('✅ Notificaciones activadas correctamente!');
      updateNotificationIndicator();
    }
  } catch (error) {
    console.error('Error requesting permission:', error);
    alert('❌ Error al activar notificaciones');
  }
}

// Function to send notification
async function sendOneSignalNotification(buyer, product, amount) {
  // This will be called from your backend or Firebase function
  // For now, we'll just log it
  console.log('Would send OneSignal notification:', { buyer, product, amount });
}
