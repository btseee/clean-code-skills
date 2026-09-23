class SubscriptionsController < ApplicationController
  def charge
    subscription = Subscription.find(params[:id])
    subscription.charge!(params[:amount].to_f)
    redirect_to subscription
  end
end
