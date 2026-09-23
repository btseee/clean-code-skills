class Subscription < ApplicationRecord
  belongs_to :customer

  def charge!(amount)
    PaymentGateway.charge(customer.card_token, amount)
    update!(last_charged_at: Time.current)
  end
end
