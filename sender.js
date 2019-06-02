cb.onTip(function(tip){
	var user = 'TaterTot1234'
	tip['date'] = Date.now()
	cb.sendNotice(JSON.stringify(tip), to_user=user)
});
