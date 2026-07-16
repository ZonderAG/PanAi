FROM ros:jazzy-ros-base AS builder

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-diagnostic-updater \
    ros-jazzy-diagnostic-aggregator \
    ros-jazzy-rosbag2-storage-mcap \
    ros-jazzy-message-filters \
    ros-jazzy-ros-gz \
    ros-jazzy-teleop-twist-keyboard \
    python3-serial \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /panai_ws

# Копирование исходников
COPY src/ ./src/

# Сборка рабочего пространства
RUN . /opt/ros/jazzy/setup.sh && \
    colcon build --symlink-install

FROM ros:jazzy-ros-base AS runtime

# Установка рантайм зависимостей и Python-библиотек
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-numpy \
    python3-opencv \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-diagnostic-updater \
    ros-jazzy-diagnostic-aggregator \
    ros-jazzy-rosbag2-storage-mcap \
    ros-jazzy-message-filters \
    ros-jazzy-ros-gz \
    ros-jazzy-teleop-twist-keyboard \
    && rm -rf /var/lib/apt/lists/*

# CycloneDDS как транспорт по умолчанию
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

WORKDIR /panai_ws

# Копируем только скомпилированные артефакты
COPY --from=builder /panai_ws/install /panai_ws/install
COPY --from=builder /panai_ws/build /panai_ws/build
# Для разработки мы будем монтировать src/ в docker-compose, 
# но базовая версия тоже копируется для самодостаточности вне compose.
COPY --from=builder /panai_ws/src /panai_ws/src

# Настройка Entrypoint
RUN echo "#!/bin/bash\nset -e\nsource /opt/ros/jazzy/setup.bash\nif [ -f /panai_ws/install/setup.bash ]; then source /panai_ws/install/setup.bash; fi\nexec \"\$@\"" > /ros_entrypoint.sh \
    && chmod +x /ros_entrypoint.sh

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]
