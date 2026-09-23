class ReceiptMailer < ApplicationMailer
  def receipt(invoice)
    @invoice = invoice
    mail(to: @invoice.subscription.customer.email, subject: "Your receipt")
  end
end
