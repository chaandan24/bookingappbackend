"""
Email Service
Handles sending emails for various notifications
"""

from flask import current_app, render_template_string
from flask_mail import Message
import os
from extensions import mail



class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_email(to, subject, html_body, text_body=None):
        """Send an email"""
        try:
            msg = Message(
                subject=subject,
                recipients=[to] if isinstance(to, str) else to,
                html=html_body,
                body=text_body or html_body
            )
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to send email: {str(e)}')
            return False
    
    @staticmethod
    def send_registration_email(user):
        """Send welcome email after registration"""
        subject = "Welcome to Airbnb Clone!"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF5A5F;">Welcome to (name), {user.first_name}! 🎉</h2>
                <p>Thank you for joining our community!</p>
                <p>Your account has been successfully created with the following details:</p>
                <ul>
                    <li><strong>Username:</strong> {user.username}</li>
                    <li><strong>Email:</strong> {user.email}</li>
                </ul>
                <p>You can now start exploring amazing properties or list your own!</p>
                <div style="margin: 30px 0;">
                    <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}" 
                       style="background-color: #FF5A5F; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Explore Properties
                    </a>
                </div>
                <p style="color: #666; font-size: 14px;">
                    If you have any questions, feel free to contact our support team.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_body)
    
    @staticmethod
    def send_booking_confirmation(booking, guest, property_obj, host):
        """Send booking confirmation email to guest"""
        subject = f"Booking Confirmation - {property_obj.title}"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF5A5F;">Booking Confirmed! ✓</h2>
                <p>Hi {guest.first_name},</p>
                <p>Your booking has been confirmed!</p>
                
                <div style="background-color: #f8f8f8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #333;">{property_obj.title}</h3>
                    <p><strong>Location:</strong> {property_obj.city}, {property_obj.country}</p>
                    <p><strong>Check-in:</strong> {booking.check_in}</p>
                    <p><strong>Check-out:</strong> {booking.check_out}</p>
                    <p><strong>Guests:</strong> {booking.guests}</p>
                    <p><strong>Total Price:</strong> ${booking.total_price}</p>
                    <p><strong>Booking ID:</strong> #{booking.id}</p>
                </div>
                
                <h3>Host Information</h3>
                <p><strong>Host:</strong> {host.full_name}</p>
                
                <div style="margin: 30px 0;">
                    <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/bookings/{booking.id}" 
                       style="background-color: #FF5A5F; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Booking Details
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    We hope you have a wonderful stay!
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        return EmailService.send_email(guest.email, subject, html_body)
    
    @staticmethod
    def send_booking_notification_to_host(booking, guest, property_obj, host):
        """Send new booking notification to host"""
        subject = f"New Booking - {property_obj.title}"
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF5A5F;">New Booking Received! 🎉</h2>
                <p>Hi {host.first_name},</p>
                <p>You have a new booking for your property!</p>
                
                <div style="background-color: #f8f8f8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #333;">{property_obj.title}</h3>
                    <p><strong>Guest:</strong> {guest.full_name}</p>
                    <p><strong>Check-in:</strong> {booking.check_in}</p>
                    <p><strong>Check-out:</strong> {booking.check_out}</p>
                    <p><strong>Guests:</strong> {booking.guests}</p>
                    <p><strong>Total Earnings:</strong> ${booking.total_price}</p>
                    <p><strong>Booking ID:</strong> #{booking.id}</p>
                </div>
                
                <div style="margin: 30px 0;">
                    <a href="{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/host/bookings/{booking.id}" 
                       style="background-color: #FF5A5F; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Booking Details
                    </a>
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    Make sure to prepare your property for the guest's arrival.
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        return EmailService.send_email(host.email, subject, html_body)
    
    @staticmethod
    def send_cancellation_email(booking, user, property_obj, is_host=False):
        """Send cancellation email"""
        subject = f"Booking Cancelled - {property_obj.title}"
        recipient_name = user.first_name
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF5A5F;">Booking Cancelled</h2>
                <p>Hi {recipient_name},</p>
                <p>A booking has been cancelled.</p>
                
                <div style="background-color: #f8f8f8; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #333;">{property_obj.title}</h3>
                    <p><strong>Check-in:</strong> {booking.check_in}</p>
                    <p><strong>Check-out:</strong> {booking.check_out}</p>
                    <p><strong>Booking ID:</strong> #{booking.id}</p>
                    {f'<p><strong>Reason:</strong> {booking.cancellation_reason}</p>' if booking.cancellation_reason else ''}
                </div>
                
                <p style="color: #666; font-size: 14px;">
                    {'The dates are now available for new bookings.' if is_host else 'You can book another property anytime.'}
                </p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_body)
    
    @staticmethod
    def send_verification_email(user, verification_token):
        """Send email verification email"""
        subject = "Verify Your Email"
        verify_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5001')}/verification/verify-email?token={verification_token}"
    
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF5A5F;">Verify Your Email Address</h2>
               <p>Hi {user.first_name},</p>
                <p>Thank you for registering! Please verify your email address to complete your registration:</p>
            
                <div style="margin: 30px 0;">
                    <a href="{verify_url}" 
                       style="background-color: #FF5A5F; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Verify Email
                    </a>
                </div>
            
                <p>Or copy and paste this link into your browser:</p>
                <p style="background-color: #f8f8f8; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {verify_url}
                </p>
            
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This link will expire in 24 hours.
                </p>
            
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_body)
    
    @staticmethod
    def send_password_reset_email(user, reset_token):
        """Send password reset email"""
        subject = "Reset Your Password"
        reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #FF5A5F;">Password Reset Request</h2>
                <p>Hi {user.first_name},</p>
                <p>We received a request to reset your password. Click the button below to create a new password:</p>
                
                <div style="margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background-color: #FF5A5F; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="background-color: #f8f8f8; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {reset_url}
                </p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This link will expire in 1 hour for security reasons.
                </p>
                
                <p style="color: #666; font-size: 14px;">
                    If you didn't request a password reset, please ignore this email or contact support if you have concerns.
                </p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    This is an automated message. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_body)
