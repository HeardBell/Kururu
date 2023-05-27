FROM nginx:1.23-alpine

# nginx_lb_active_active.conf or nginx_lb_active_passive.conf
COPY active-passive.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
